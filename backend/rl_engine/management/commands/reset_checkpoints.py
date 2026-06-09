"""Reset (zero) on-disk policy checkpoints.

The original checkpoints diverged to ~1e17 because the old policy regressed raw
dollar prices with unbounded SGD. This command rewrites every checkpoint to a
clean zero-initialized state compatible with the stable OnlinePolicy.
"""
from __future__ import annotations

import json

from django.conf import settings
from django.core.management.base import BaseCommand

DEFAULT_LR = 0.05


class Command(BaseCommand):
    help = "Zero-initialize policy checkpoints for all tickers/horizons."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--all-default",
            action="store_true",
            help="Also create fresh checkpoints for PREDICTION_DEFAULT_TICKERS x horizons.",
        )

    def handle(self, *args, **options) -> None:
        root = settings.CHECKPOINT_STORAGE_PATH
        root.mkdir(parents=True, exist_ok=True)
        count = 0

        # Rewrite every existing checkpoint to zeros.
        for path in root.glob("*/*.json"):
            ticker = path.parent.name
            horizon = path.stem
            self._write(root, ticker, horizon)
            count += 1

        if options.get("all_default"):
            for ticker in settings.PREDICTION_DEFAULT_TICKERS:
                for horizon in settings.PREDICTION_HORIZONS:
                    path = root / ticker / f"{horizon}.json"
                    if not path.exists():
                        self._write(root, ticker, horizon)
                        count += 1

        self.stdout.write(self.style.SUCCESS(f"Reset {count} checkpoint(s)."))

    @staticmethod
    def _write(root, ticker: str, horizon: str) -> None:
        path = root / ticker / f"{horizon}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ticker": ticker,
            "horizon": horizon,
            "weights": [0.0, 0.0, 0.0],
            "bias": 0.0,
            "learning_rate": DEFAULT_LR,
        }
        path.write_text(json.dumps(payload, indent=2))
