"""WebSocket routing for reinforcement learning predictions."""
from __future__ import annotations

from django.urls import path

from .consumers import PredictionConsumer

websocket_urlpatterns = [
    path("ws/predictions/<str:ticker>/<str:horizon>/", PredictionConsumer.as_asgi()),
]
