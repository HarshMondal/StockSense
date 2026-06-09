"""URL configuration for market data REST endpoints."""
from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.search_view, name="market-search"),
    path("market/<str:ticker>/snapshot/", views.snapshot_view, name="market-snapshot"),
]
