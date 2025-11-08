"""URL routing for market data websockets."""
from __future__ import annotations

from django.urls import path

from .consumers import MarketStreamConsumer

websocket_urlpatterns = [
    path("ws/stream/<str:symbol>/", MarketStreamConsumer.as_asgi()),
]
