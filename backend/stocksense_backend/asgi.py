"""ASGI config for Stocksense backend."""
from __future__ import annotations

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from market_data.routing import websocket_urlpatterns as market_ws
from rl_engine.routing import websocket_urlpatterns as rl_ws

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stocksense_backend.settings.dev")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                market_ws
                + rl_ws
            )
        ),
    }
)
