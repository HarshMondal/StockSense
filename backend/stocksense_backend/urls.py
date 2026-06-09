"""Root URL configuration."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("market_data.urls")),
    path("api/", include("rl_engine.urls")),
    path("api/", include("analytics.urls")),
    path("api/", include("metadata.urls")),
]
