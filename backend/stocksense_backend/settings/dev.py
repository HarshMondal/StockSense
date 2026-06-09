"""Development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True

# Session/CSRF cookies for a same-site SPA (localhost:5173 <-> localhost:8000).
# SameSite is computed on the registrable domain (localhost), so 'Lax' works
# across ports in dev without requiring SameSite=None/Secure.
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
