"""URL configuration for metadata endpoints."""
from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("meta/model-card/", views.model_card_view, name="meta-model-card"),
    path("meta/provenance/", views.provenance_view, name="meta-provenance"),
    path("meta/version/", views.version_view, name="meta-version"),
]
