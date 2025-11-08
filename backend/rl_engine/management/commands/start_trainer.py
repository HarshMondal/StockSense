"""Run the continual learning trainer."""
from __future__ import annotations

import asyncio
import logging
from random import random
from typing import Iterable

from django.core.management.base import BaseCommand

from market_data.services import FinnhubClient
from stocksense_backend.settings.base import PREDICTION_DEFAULT_TICKERS, PREDICTION_HORIZONS

from ...services import ENGINE

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Starts the online reinforcement learning trainer loop."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Update interval in seconds",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        asyncio.run(run_trainer(interval))


async def run_trainer(interval: int) -> None:
    client = FinnhubClient()
    tickers = PREDICTION_DEFAULT_TICKERS or ["AAPL"]
    horizons = PREDICTION_HORIZONS or ["intraday"]
    try:
        while True:
            for ticker in tickers:
                quote = await client.fetch_quote(ticker)
                features = _feature_vector_from_quote(quote.price)
                target = quote.price * (1 + random() * 0.01)
                for horizon in horizons:
                    prediction = ENGINE.update_policy(ticker, horizon, features, target)
                    LOGGER.info(
                        "Updated %s/%s at %s", ticker, horizon, prediction.updated_at.isoformat()
                    )
            await asyncio.sleep(interval)
    finally:
        await client.aclose()


def _feature_vector_from_quote(price: float) -> Iterable[float]:
    return [price, price * 0.5, price * 0.1]
