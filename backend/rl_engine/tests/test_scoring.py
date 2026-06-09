"""Tests for the baseline-scoring helpers used by the prediction loop."""
from __future__ import annotations

from rl_engine.loop import _same_sign, _stddev


def test_same_sign_directional():
    assert _same_sign(0.01, 0.02) is True       # both up
    assert _same_sign(-0.01, -0.5) is True       # both down
    assert _same_sign(0.01, -0.02) is False      # opposite
    assert _same_sign(0.0, 0.0) is True          # both flat
    assert _same_sign(0.01, 0.0) is False        # up vs flat


def test_stddev_basic():
    assert _stddev([]) == 0.0
    assert _stddev([1.0]) == 0.0
    s = _stddev([1.0, 1.0, 1.0])
    assert abs(s) < 1e-12
    s2 = _stddev([0.0, 2.0])
    assert abs(s2 - 1.4142135623730951) < 1e-9
