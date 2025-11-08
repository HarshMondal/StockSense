"""WebSocket consumers for market data."""
from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime
from typing import Any, Dict

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .services import websocket_stream


class MarketStreamConsumer(AsyncJsonWebsocketConsumer):
    """Broadcast Finnhub ticks to subscribed clients."""

    async def connect(self) -> None:  # pragma: no cover - framework integration
        self.symbol = self.scope["url_route"]["kwargs"]["symbol"].upper()
        await self.accept()
        self._task = asyncio.create_task(self._stream())

    async def disconnect(self, close_code: int) -> None:  # pragma: no cover
        if hasattr(self, "_task"):
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def receive_json(self, content: Dict[str, Any], **kwargs: Any) -> None:
        command = content.get("command")
        if command == "ping":
            await self.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

    async def _stream(self) -> None:
        try:
            async for quote in websocket_stream(self.symbol):
                await self.send_json(
                    {
                        "type": "tick",
                        "symbol": quote.symbol,
                        "price": quote.price,
                        "volume": quote.volume,
                        "timestamp": quote.timestamp.isoformat(),
                    }
                )
        except asyncio.CancelledError:  # pragma: no cover
            raise
        except Exception as exc:  # pragma: no cover
            await self.send_json(
                {
                    "type": "error",
                    "message": f"stream_error:{exc}",
                }
            )
