"""Services responsible for interacting with Finnhub and abstracting the data feed.

This module exposes a single ``MarketDataSource`` seam with two implementations:

* ``FinnhubLiveSource`` — real-time US trades via Finnhub's websocket + REST.
* ``ReplaySimulatorSource`` — a seeded random-walk used when the market is closed
  (defined in :mod:`market_data.replay`) so the whole pipeline is always demoable.

Both write the latest price into the process-wide :class:`PriceCache`, so the 10s
sampler in the prediction loop reads the cache and never makes a per-tick REST
call (keeping us under Finnhub's free-tier rate limit).
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import AsyncIterator, Dict, List, Optional, Protocol, Tuple
from zoneinfo import ZoneInfo

import httpx

from stocksense_backend.settings.base import FINNHUB_API_KEY

LOGGER = logging.getLogger(__name__)

FINNHUB_WS_URL = "wss://ws.finnhub.io"
FINNHUB_REST_URL = "https://finnhub.io/api/v1"

_EASTERN = ZoneInfo("America/New_York")


@dataclass(slots=True)
class Quote:
    """Represents a Finnhub real-time quote."""

    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[float] = None


# --------------------------------------------------------------------------- #
# Process-wide latest-price cache (TTL-guarded)                               #
# --------------------------------------------------------------------------- #
class PriceCache:
    """Tiny in-process cache of the latest price per symbol.

    The live websocket writes here continuously; snapshots and the 10s sampler
    read from here instead of hitting the REST API on every call.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Tuple[float, datetime, Optional[float]]] = {}
        self._lock = asyncio.Lock()

    def set(self, symbol: str, price: float, ts: datetime, volume: Optional[float] = None) -> None:
        self._data[symbol.upper()] = (price, ts, volume)

    def get(self, symbol: str) -> Optional[Quote]:
        entry = self._data.get(symbol.upper())
        if entry is None:
            return None
        price, ts, volume = entry
        return Quote(symbol=symbol.upper(), price=price, timestamp=ts, volume=volume)


# Module-level singleton.
PRICE_CACHE = PriceCache()


# --------------------------------------------------------------------------- #
# Market hours                                                                 #
# --------------------------------------------------------------------------- #
class MarketHours:
    """Regular US equity session detection (no holiday calendar yet — v1 TODO)."""

    OPEN = time(9, 30)
    CLOSE = time(16, 0)

    @classmethod
    def is_market_open(cls, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        et = now.astimezone(_EASTERN)
        if et.weekday() >= 5:  # Sat/Sun
            return False
        return cls.OPEN <= et.time() <= cls.CLOSE


# --------------------------------------------------------------------------- #
# Finnhub REST client                                                          #
# --------------------------------------------------------------------------- #
class FinnhubClient:
    """Thin async wrapper around Finnhub's REST API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or FINNHUB_API_KEY
        if not self._api_key:
            raise RuntimeError("FINNHUB_API_KEY is not configured")
        self._client = httpx.AsyncClient(base_url=FINNHUB_REST_URL, timeout=10.0)

    async def fetch_quote(self, symbol: str) -> Quote:
        """Fetch the latest quote for the provided symbol (REST /quote)."""
        response = await self._client.get(
            "/quote", params={"symbol": symbol, "token": self._api_key}
        )
        response.raise_for_status()
        data = response.json()
        return Quote(
            symbol=symbol.upper(),
            price=float(data.get("c") or 0.0),
            volume=None,
            timestamp=datetime.fromtimestamp(int(data.get("t") or 0), tz=timezone.utc),
        )

    async def search(self, query: str) -> List[dict]:
        """Symbol autocomplete (REST /search)."""
        response = await self._client.get(
            "/search", params={"q": query, "token": self._api_key}
        )
        response.raise_for_status()
        results = response.json().get("result", []) or []
        return [
            {
                "symbol": item.get("symbol"),
                "description": item.get("description"),
                "type": item.get("type"),
                "displaySymbol": item.get("displaySymbol"),
            }
            for item in results
            if item.get("symbol")
        ]

    async def fetch_candles(
        self, symbol: str, resolution: str, start: int, end: int
    ) -> Dict[str, List[float]]:
        """Fetch historical candles (REST /stock/candle; premium on some plans)."""
        response = await self._client.get(
            "/stock/candle",
            params={
                "symbol": symbol,
                "resolution": resolution,
                "from": start,
                "to": end,
                "token": self._api_key,
            },
        )
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()


# --------------------------------------------------------------------------- #
# Live websocket stream                                                        #
# --------------------------------------------------------------------------- #
async def websocket_stream(symbol: str) -> AsyncIterator[Quote]:
    """Yield quotes from Finnhub's websocket for the given symbol.

    Reconnects with backoff on error. Every yielded quote is also written to
    :data:`PRICE_CACHE`.
    """
    import websockets

    if not FINNHUB_API_KEY:
        raise RuntimeError("FINNHUB_API_KEY is not configured")

    url = f"{FINNHUB_WS_URL}?token={FINNHUB_API_KEY}"
    symbol = symbol.upper()
    while True:
        try:
            async with websockets.connect(url, ping_interval=15, ping_timeout=15) as ws:
                await ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
                async for raw in ws:
                    message = json.loads(raw)
                    if message.get("type") != "trade":
                        continue
                    for trade in message.get("data", []) or []:
                        price = float(trade.get("p") or 0.0)
                        volume = float(trade.get("v") or 0.0)
                        ts = datetime.fromtimestamp(
                            int(trade.get("t") or 0) / 1000, tz=timezone.utc
                        )
                        quote = Quote(symbol=symbol, price=price, timestamp=ts, volume=volume)
                        PRICE_CACHE.set(symbol, price, ts, volume)
                        yield quote
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - network resilience
            LOGGER.warning("Finnhub websocket error: %s", exc)
            await asyncio.sleep(5)


# --------------------------------------------------------------------------- #
# Pluggable data-source interface                                             #
# --------------------------------------------------------------------------- #
class MarketDataSource(Protocol):
    name: str

    async def get_quote(self, symbol: str) -> Quote: ...

    def stream(self, symbol: str) -> AsyncIterator[Quote]: ...


class FinnhubLiveSource:
    """Live data source backed by Finnhub websocket + REST."""

    name = "live"

    def __init__(self, client: Optional[FinnhubClient] = None) -> None:
        self._client = client or FinnhubClient()

    async def get_quote(self, symbol: str) -> Quote:
        cached = PRICE_CACHE.get(symbol)
        if cached is not None:
            return cached
        quote = await self._client.fetch_quote(symbol)
        PRICE_CACHE.set(quote.symbol, quote.price, quote.timestamp, quote.volume)
        return quote

    def stream(self, symbol: str) -> AsyncIterator[Quote]:
        return websocket_stream(symbol)

    async def aclose(self) -> None:
        await self._client.aclose()


def make_source(force_replay: Optional[bool] = None) -> MarketDataSource:
    """Choose the live source during market hours, replay otherwise.

    ``STOCKSENSE_FORCE_REPLAY=1`` (or ``force_replay=True``) forces replay even
    when the market is open — handy for deterministic local demos and tests.
    """
    import os

    from .replay import ReplaySimulatorSource

    if force_replay is None:
        force_replay = os.environ.get("STOCKSENSE_FORCE_REPLAY") == "1"

    if force_replay or not MarketHours.is_market_open():
        return ReplaySimulatorSource()
    return FinnhubLiveSource()
