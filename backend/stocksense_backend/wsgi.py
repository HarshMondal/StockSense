"""WSGI config for Stocksense backend."""
from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stocksense_backend.settings.dev")

application = get_wsgi_application()
