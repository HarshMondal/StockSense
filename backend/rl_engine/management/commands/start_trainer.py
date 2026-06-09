"""Run the continual-learning trainer headlessly for the default tickers.

Keeps the online policies learning (and checkpoints/PredictionLog fresh) even when
no browser is attached. With the Redis channel layer, its broadcasts also reach
live dashboards in other processes; with the in-memory layer it simply trains.
"""
from __future__ import annotations

import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from rl_engine.loop import LOOP_MANAGER

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start the online learning trainer loop for default tickers/horizons."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--tickers", nargs="*", default=None,
            help="Override tickers (default: PREDICTION_DEFAULT_TICKERS).",
        )
        parser.add_argument(
            "--horizons", nargs="*", default=None,
            help="Override horizons (default: PREDICTION_HORIZONS).",
        )

    def handle(self, *args, **options) -> None:
        tickers = options.get("tickers") or settings.PREDICTION_DEFAULT_TICKERS
        horizons = options.get("horizons") or settings.PREDICTION_HORIZONS
        self.stdout.write(f"Training {tickers} x {horizons} (Ctrl-C to stop)…")
        try:
            asyncio.run(self._run(tickers, horizons))
        except KeyboardInterrupt:  # pragma: no cover
            self.stdout.write("Stopped.")

    async def _run(self, tickers, horizons) -> None:
        for ticker in tickers:
            for horizon in horizons:
                await LOOP_MANAGER.acquire(ticker, horizon)
        # Keep loops alive indefinitely.
        while True:
            await asyncio.sleep(3600)
