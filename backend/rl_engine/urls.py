"""URL configuration for RL prediction REST endpoints."""
from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path(
        "predictions/<str:ticker>/<str:horizon>/snapshot/",
        views.prediction_snapshot_view,
        name="prediction-snapshot",
    ),
    path(
        "predictions/<str:ticker>/<str:horizon>/history/",
        views.prediction_history_view,
        name="prediction-history",
    ),
    path(
        "predictions/<str:ticker>/<str:horizon>/accuracy/",
        views.accuracy_view,
        name="prediction-accuracy",
    ),
]
