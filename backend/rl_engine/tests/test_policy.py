"""Regression tests for the numerically stable OnlinePolicy.

These guard against the original ~1e17 divergence bug ever returning.
"""
from __future__ import annotations

import math
import random

from rl_engine.services import OnlinePolicy


def test_policy_stays_bounded_under_adversarial_updates():
    policy = OnlinePolicy(ticker="TEST", horizon="intraday")
    rng = random.Random(42)
    for _ in range(10_000):
        features = [rng.uniform(-5, 5) for _ in range(3)]
        target = rng.uniform(-0.5, 0.5)  # deliberately outside the +/-5% clamp
        policy.update(features, target)

    assert all(math.isfinite(w) for w in policy.weights)
    assert math.isfinite(policy.bias)
    assert max(abs(w) for w in policy.weights) < 10.0
    assert abs(policy.bias) < 10.0


def test_predict_is_clamped_to_max_return():
    policy = OnlinePolicy(weights=[1e3, 1e3, 1e3], bias=1e3)
    r = policy.predict([100.0, 100.0, 100.0])
    assert -policy.max_return <= r <= policy.max_return


def test_deserialize_heals_diverged_checkpoint():
    payload = {
        "ticker": "AAPL",
        "horizon": "intraday",
        "weights": [5.18e17, 2.59e17, 5.18e16],
        "bias": 1.93e15,
        "learning_rate": 0.05,
    }
    policy = OnlinePolicy.deserialize(payload)
    assert policy.weights == [0.0, 0.0, 0.0]
    assert policy.bias == 0.0


def test_nan_target_does_not_poison_weights():
    policy = OnlinePolicy()
    policy.update([float("nan"), 1.0, 1.0], 0.01)
    assert all(math.isfinite(w) for w in policy.weights)
