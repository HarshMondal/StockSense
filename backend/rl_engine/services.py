"""Simplified reinforcement learning engine abstractions."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

from stocksense_backend.settings.base import CHECKPOINT_STORAGE_PATH

LOGGER = logging.getLogger(__name__)


@dataclass
class Prediction:
    """Represents a prediction output for the frontend."""

    ticker: str
    horizon: str
    prices: List[Tuple[float, float]]  # (timestamp, price)
    confidence: float
    updated_at: datetime

    def as_dict(self) -> Dict[str, object]:
        return {
            "ticker": self.ticker,
            "horizon": self.horizon,
            "points": self.prices,
            "confidence": self.confidence,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class OnlinePolicy:
    """A light-weight online learner approximating RL behaviour."""

    ticker: str
    horizon: str
    weights: List[float] = field(default_factory=lambda: [0.5, 0.3, 0.2])
    bias: float = 0.0
    learning_rate: float = 0.05

    def update(self, features: Iterable[float], target: float) -> None:
        """Apply a simple gradient step resembling policy improvement."""
        features_array = np.array(list(features))
        prediction = float(np.dot(self.weights, features_array) + self.bias)
        error = target - prediction
        self.weights = list(self.weights + self.learning_rate * error * features_array)
        self.bias += self.learning_rate * error

    def predict(self, features: Iterable[float]) -> float:
        features_array = np.array(list(features))
        return float(np.dot(self.weights, features_array) + self.bias)

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
        return cls(
            ticker=str(payload["ticker"]),
            horizon=str(payload["horizon"]),
            weights=list(payload.get("weights", [0.5, 0.3, 0.2])),
            bias=float(payload.get("bias", 0.0)),
            learning_rate=float(payload.get("learning_rate", 0.05)),
        )


class PredictionEngine:
    """Coordinates online policy updates and checkpoint persistence."""

    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = storage_root or CHECKPOINT_STORAGE_PATH
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self._policies: Dict[Tuple[str, str], OnlinePolicy] = {}

    def load_policy(self, ticker: str, horizon: str) -> OnlinePolicy:
        key = (ticker.upper(), horizon)
        if key not in self._policies:
            policy = self._load_from_disk(*key)
            self._policies[key] = policy
        return self._policies[key]

    def _load_from_disk(self, ticker: str, horizon: str) -> OnlinePolicy:
        checkpoint_file = self._checkpoint_path(ticker, horizon)
        if checkpoint_file.exists():
            payload = json.loads(checkpoint_file.read_text())
            LOGGER.info("Loaded checkpoint for %s %s", ticker, horizon)
            return OnlinePolicy.deserialize(payload)
        return OnlinePolicy(ticker=ticker, horizon=horizon)

    def _checkpoint_path(self, ticker: str, horizon: str) -> Path:
        ticker_dir = self.storage_root / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)
        return ticker_dir / f"{horizon}.json"

    def update_policy(self, ticker: str, horizon: str, features: Iterable[float], target: float) -> Prediction:
        policy = self.load_policy(ticker, horizon)
        policy.update(features, target)
        self._save_policy(policy)
        return self._build_prediction(policy, features)

    def predict(self, ticker: str, horizon: str, features: Iterable[float]) -> Prediction:
        policy = self.load_policy(ticker, horizon)
        return self._build_prediction(policy, features)

    def _build_prediction(self, policy: OnlinePolicy, features: Iterable[float]) -> Prediction:
        predicted_value = policy.predict(features)
        now = datetime.utcnow()
        # Dummy projection for next 5 intervals using simple drift assumption
        points = []
        for idx, delta in enumerate([1, 2, 3, 4, 5], start=1):
            points.append((now.timestamp() + idx * 60, predicted_value * (1 + 0.01 * idx)))
        confidence = min(0.99, max(0.1, 0.5 + policy.bias))
        return Prediction(
            ticker=policy.ticker,
            horizon=policy.horizon,
            prices=points,
            confidence=confidence,
            updated_at=now,
        )

    def _save_policy(self, policy: OnlinePolicy) -> None:
        checkpoint_file = self._checkpoint_path(policy.ticker, policy.horizon)
        checkpoint_file.write_text(json.dumps(policy.serialize(), indent=2))
        LOGGER.info("Saved checkpoint for %s %s", policy.ticker, policy.horizon)


ENGINE = PredictionEngine()
