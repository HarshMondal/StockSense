"""Replay / simulator data source for when the US market is closed.

Emits a seeded random-walk of ticks so the dashboard and the predict->observe->
update loop are always demoable. Writes the same :data:`PRICE_CACHE` as the live
source, so downstream code (the 10s sampler) is identical regardless of source.
"""
from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Dict, Optional

from .services import PRICE_CACHE, Quote

LOGGER = logging.getLogger(__name__)

# Rough seed prices so a cold start (no network) still produces a believable line.
_SEED_PRICES: Dict[str, float] = {
    "AAPL": 195.0,
    "MSFT": 420.0,
    "GOOG": 175.0,
    "AMZN": 185.0,
    "NVDA": 120.0,
    "TSLA": 250.0,
    "META": 500.0,
}
_DEFAULT_SEED = 100.0

# Per-tick volatility (~0.04%); tick cadence in seconds.
_SIGMA = 0.0004
_TICK_SECONDS = 1.0
_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "replay"


def _seed_price(symbol: str) -> float:
    cached = PRICE_CACHE.get(symbol)
    if cached is not None and cached.price > 0:
        return cached.price
    return _SEED_PRICES.get(symbol.upper(), _DEFAULT_SEED)


def _load_fixture(symbol: str) -> Optional[list]:
    """Load recorded ticks from fixtures/replay/<symbol>.jsonl if present."""
    path = _FIXTURE_DIR / f"{symbol.upper()}.jsonl"
    if not path.exists():
        return None
    import json

    ticks = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            ticks.append(json.loads(line))
    return ticks or None


class ReplaySimulatorSource:
    """Market-closed source: replays recorded ticks or simulates a random walk."""

    name = "replay"

    async def get_quote(self, symbol: str) -> Quote:
        price = _seed_price(symbol)
        ts = datetime.now(timezone.utc)
        quote = Quote(symbol=symbol.upper(), price=price, timestamp=ts, volume=None)
        PRICE_CACHE.set(quote.symbol, price, ts, None)
        return quote

    async def stream(self, symbol: str) -> AsyncIterator[Quote]:
        symbol = symbol.upper()
        fixture = _load_fixture(symbol)
        # Deterministic per-symbol RNG for reproducible demos/tests.
        rng = random.Random(hash(symbol) & 0xFFFFFFFF)
        price = _seed_price(symbol)
        i = 0
        while True:
            if fixture:
                row = fixture[i % len(fixture)]
                price = float(row.get("price", price))
                volume = row.get("volume")
            else:
                price = max(0.01, price * (1.0 + rng.gauss(0.0, _SIGMA)))
                volume = float(rng.randint(50, 500))
            ts = datetime.now(timezone.utc)
            PRICE_CACHE.set(symbol, price, ts, volume)
            yield Quote(symbol=symbol, price=price, timestamp=ts, volume=volume)
            i += 1
            await asyncio.sleep(_TICK_SECONDS)
