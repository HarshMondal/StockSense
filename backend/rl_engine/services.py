"""Online learning engine: a numerically stable incremental policy + checkpoint IO.

The policy predicts a *bounded fractional return* for t+horizon (NOT a raw price).
This is the fix for the original divergence: the old policy regressed raw dollar
prices with unbounded SGD and exploded to ~1e17. Here the target is O(0.01), the
features are O(1), the gradient is norm-clipped, and weight decay keeps weights O(1).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

from stocksense_backend.settings.base import CHECKPOINT_STORAGE_PATH

LOGGER = logging.getLogger(__name__)

N_FEATURES = 3
# Sanity bound: any |weight| above this means a corrupt/diverged checkpoint.
_SANE_WEIGHT = 1e6


def _fit_features(features: Iterable[float]) -> np.ndarray:
    vec = [float(v) for v in features]
    if len(vec) < N_FEATURES:
        vec.extend([0.0] * (N_FEATURES - len(vec)))
    return np.asarray(vec[:N_FEATURES], dtype=float)


@dataclass
class OnlinePolicy:
    """A lightweight online learner approximating adaptive forecasting behaviour."""

    ticker: str = ""
    horizon: str = ""
    weights: List[float] = field(default_factory=lambda: [0.0] * N_FEATURES)
    bias: float = 0.0
    learning_rate: float = 0.05
    max_return: float = 0.05      # clamp predictions/targets to +/-5%
    grad_clip: float = 1.0        # max gradient L2 norm per step
    weight_decay: float = 1e-4

    def predict(self, features: Iterable[float]) -> float:
        """Return a bounded fractional return r_hat for t+horizon."""
        x = _fit_features(features)
        r = float(np.dot(self.weights, x) + self.bias)
        if not np.isfinite(r):
            return 0.0
        return float(np.clip(r, -self.max_return, self.max_return))

    def update(self, features: Iterable[float], actual_return: float) -> None:
        """One clipped SGD step toward the observed return."""
        x = _fit_features(features)
        r_hat = float(np.dot(self.weights, x) + self.bias)
        err = float(np.clip(r_hat - actual_return, -self.max_return, self.max_return))

        grad = err * x
        norm = float(np.linalg.norm(grad))
        if norm > self.grad_clip:
            grad = grad * (self.grad_clip / norm)

        weights = np.asarray(self.weights, dtype=float)
        weights = weights * (1.0 - self.learning_rate * self.weight_decay)
        weights = weights - self.learning_rate * grad
        self.weights = [float(v) for v in weights]
        self.bias = float(self.bias - self.learning_rate * err)

        if not (np.all(np.isfinite(self.weights)) and np.isfinite(self.bias)):
            # NaN/inf guard: re-initialize rather than poison the checkpoint.
            self.weights = [0.0] * N_FEATURES
            self.bias = 0.0

    def serialize(self) -> Dict[str, object]:
        return {
            "ticker": self.ticker,
            "horizon": self.horizon,
            "weights": self.weights,
            "bias": self.bias,
            "learning_rate": self.learning_rate,
        }

    @classmethod
    def deserialize(cls, payload: Dict[str, object]) -> "OnlinePolicy":
        weights = [float(v) for v in payload.get("weights", [0.0] * N_FEATURES)]
        bias = float(payload.get("bias", 0.0))
        # Auto-heal diverged/corrupt checkpoints on load.
        if not np.all(np.isfinite(weights)) or max(abs(w) for w in weights) > _SANE_WEIGHT \
                or not np.isfinite(bias) or abs(bias) > _SANE_WEIGHT:
            LOGGER.warning(
                "Resetting diverged checkpoint for %s/%s",
                payload.get("ticker"), payload.get("horizon"),
            )
            weights, bias = [0.0] * N_FEATURES, 0.0
        return cls(
            ticker=str(payload.get("ticker", "")),
            horizon=str(payload.get("horizon", "")),
            weights=weights,
            bias=bias,
            learning_rate=float(payload.get("learning_rate", 0.05)),
        )


class PredictionEngine:
    """Owns the in-memory policies and their on-disk checkpoints."""

    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = Path(storage_root or CHECKPOINT_STORAGE_PATH)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self._policies: Dict[Tuple[str, str], OnlinePolicy] = {}

    def _checkpoint_path(self, ticker: str, horizon: str) -> Path:
        directory = self.storage_root / ticker.upper()
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{horizon}.json"

    def load_policy(self, ticker: str, horizon: str) -> OnlinePolicy:
        key = (ticker.upper(), horizon)
        if key not in self._policies:
            self._policies[key] = self._load_from_disk(ticker.upper(), horizon)
        return self._policies[key]

    def _load_from_disk(self, ticker: str, horizon: str) -> OnlinePolicy:
        path = self._checkpoint_path(ticker, horizon)
        if path.exists():
            try:
                payload = json.loads(path.read_text())
                LOGGER.info("Loaded checkpoint for %s %s", ticker, horizon)
                return OnlinePolicy.deserialize(payload)
            except (json.JSONDecodeError, ValueError) as exc:  # pragma: no cover
                LOGGER.warning("Bad checkpoint %s: %s", path, exc)
        return OnlinePolicy(ticker=ticker, horizon=horizon)

    def save_policy(self, policy: OnlinePolicy) -> None:
        path = self._checkpoint_path(policy.ticker, policy.horizon)
        path.write_text(json.dumps(policy.serialize(), indent=2))
        LOGGER.debug("Saved checkpoint for %s %s", policy.ticker, policy.horizon)


# Module-level singleton used by the loop, consumers, and views.
ENGINE = PredictionEngine()
