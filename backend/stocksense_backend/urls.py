"""Root URL configuration."""
from __future__ import annotations

from django.contrib import admin
from django.urls import path

from analytics.views import backtest_view, baselines_view, scenario_view
from metadata.views import model_card_view, provenance_view, version_view
from rl_engine.views import prediction_snapshot_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/backtest/", backtest_view, name="backtest"),
    path("api/baselines/", baselines_view, name="baselines"),
    path("api/what-if/", scenario_view, name="scenario"),
    path("api/predictions/<str:ticker>/<str:horizon>/snapshot/", prediction_snapshot_view, name="prediction-snapshot"),
    path("api/meta/model-card/", model_card_view, name="model-card"),
    path("api/meta/provenance/", provenance_view, name="provenance"),
    path("api/meta/version/", version_view, name="version"),
]
