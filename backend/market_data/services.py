"""Services responsible for interacting with Finnhub."""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

import httpx

from stocksense_backend.settings.base import FINNHUB_API_KEY

LOGGER = logging.getLogger(__name__)


FINNHUB_WS_URL = "wss://ws.finnhub.io"
FINNHUB_REST_URL = "https://finnhub.io/api/v1"


@dataclass(slots=True)
class Quote:
    """Represents a Finnhub real-time quote."""

    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[float] = None


class FinnhubClient:
    """Thin wrapper around Finnhub's REST API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or FINNHUB_API_KEY
        if not self._api_key:
            raise RuntimeError("FINNHUB_API_KEY is not configured")
        self._client = httpx.AsyncClient(base_url=FINNHUB_REST_URL, timeout=10.0)

    async def fetch_quote(self, symbol: str) -> Quote:
        """Fetch the latest quote for the provided symbol."""
        params = {"symbol": symbol, "token": self._api_key}
        response = await self._client.get("/quote", params=params)
        response.raise_for_status()
        payload = response.json()
        return Quote(
            symbol=symbol,
            price=float(payload.get("c", 0.0)),
            volume=float(payload.get("v", 0.0)) if payload.get("v") else None,
            timestamp=datetime.utcfromtimestamp(payload.get("t", 0)),
        )

    async def fetch_candles(
        self, symbol: str, resolution: str, start: int, end: int
    ) -> Dict[str, List[float]]:
        """Fetch historical candles for the given symbol and unix range."""
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": start,
            "to": end,
            "token": self._api_key,
        }
        response = await self._client.get("/stock/candle", params=params)
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()


async def websocket_stream(symbol: str) -> AsyncIterator[Quote]:
    """Yield quotes from Finnhub's websocket for the given symbol."""
    import websockets

    token = FINNHUB_API_KEY
    if not token:
        raise RuntimeError("FINNHUB_API_KEY is not configured")

    url = f"{FINNHUB_WS_URL}?token={token}"
    while True:
        try:
            async with websockets.connect(url, ping_interval=15, ping_timeout=15) as connection:
                subscribe_message = json.dumps({"type": "subscribe", "symbol": symbol})
                await connection.send(subscribe_message)
                async for raw in connection:
                    payload = json.loads(raw)
                    if payload.get("type") != "trade":
                        continue
                    for data in payload.get("data", []):
                        yield Quote(
                            symbol=data.get("s", symbol),
                            price=float(data.get("p", 0.0)),
                            volume=float(data.get("v", 0.0)),
                            timestamp=datetime.utcfromtimestamp(data.get("t", 0) / 1000),
                        )
        except asyncio.CancelledError:  # pragma: no cover
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("Finnhub websocket error: %s", exc)
            await asyncio.sleep(5)
