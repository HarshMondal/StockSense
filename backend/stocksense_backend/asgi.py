"""ASGI config for Stocksense backend."""
from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stocksense_backend.settings.dev")

# Initialize Django ASGI app early so apps are loaded before importing routing
# (which imports consumers that touch the app registry).
from django.core.asgi import get_asgi_application  # noqa: E402

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from market_data.routing import websocket_urlpatterns as market_ws  # noqa: E402
from rl_engine.routing import websocket_urlpatterns as rl_ws  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(market_ws + rl_ws))
        ),
    }
)
