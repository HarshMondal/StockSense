"""WebSocket consumer streaming RL predictions."""
from __future__ import annotations

import asyncio
import contextlib
from typing import Iterable

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .services import ENGINE


class PredictionConsumer(AsyncJsonWebsocketConsumer):
    """Continuously streams predictions for a ticker/horizon pair."""

    async def connect(self) -> None:  # pragma: no cover
        params = self.scope["url_route"]["kwargs"]
        self.ticker = params["ticker"].upper()
        self.horizon = params["horizon"]
        await self.accept()
        self._task = asyncio.create_task(self._loop())

    async def disconnect(self, close_code: int) -> None:  # pragma: no cover
        if hasattr(self, "_task"):
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "features":
            features = content.get("data", [])
            await self._send_prediction(features)

    async def _loop(self) -> None:
        while True:
            await self._send_prediction()
            await asyncio.sleep(30)

    async def _send_prediction(self, features: Iterable[float] | None = None) -> None:
        vector = (
            features
            if features and all(isinstance(v, (int, float)) for v in features)
            else [1.0, 0.5, 0.25]
        )
        prediction = ENGINE.predict(self.ticker, self.horizon, vector)
        await self.send_json({
            "type": "prediction",
            "payload": prediction.as_dict(),
        })
