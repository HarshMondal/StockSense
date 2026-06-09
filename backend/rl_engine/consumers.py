"""WebSocket consumer that relays predictions for a ticker/horizon to the browser.

Thin by design: it authenticates, joins the (ticker, horizon) group, ensures the
shared prediction loop is running, and relays broadcasts. All prediction/learning
logic lives in :mod:`rl_engine.loop` (one loop per ticker/horizon, not per socket).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from stocksense_backend.settings.base import PREDICTION_HORIZONS
from .loop import LOOP_MANAGER, group_name

LOGGER = logging.getLogger(__name__)


class PredictionConsumer(AsyncJsonWebsocketConsumer):
    """Streams predictions for a ticker/horizon pair from the shared loop."""

    async def connect(self) -> None:
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.close(code=4401)  # app-level "unauthorized"
            return

        kwargs = self.scope["url_route"]["kwargs"]
        self.ticker = kwargs["ticker"].upper()
        self.horizon = kwargs["horizon"]
        if self.horizon not in PREDICTION_HORIZONS:
            await self.close(code=4400)  # app-level "bad request"
            return

        self.group = group_name(self.ticker, self.horizon)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await LOOP_MANAGER.acquire(self.ticker, self.horizon)

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)
            await LOOP_MANAGER.release(self.ticker, self.horizon)

    async def receive_json(self, content: Dict[str, Any], **kwargs: Any) -> None:
        if content.get("command") == "ping":
            await self.send_json(
                {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
            )

    async def prediction_tick(self, event: Dict[str, Any]) -> None:
        await self.send_json(event["payload"])
