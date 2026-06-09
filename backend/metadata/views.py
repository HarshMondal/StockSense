"""Metadata endpoints: model card, data provenance, and version info."""
from __future__ import annotations

from datetime import datetime, timezone

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def model_card_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "name": "Stocksense Online Learner",
            "version": "1.0.0",
            "last_retrain": datetime.now(timezone.utc).isoformat(),
            "horizons": ["intraday", "daily", "weekly"],
            "description": (
                "An online incremental learner that predicts a bounded 10-second-ahead "
                "return from normalized price/volume/momentum features and updates itself "
                "each tick against the observed move."
            ),
            "known_risks": (
                "At a 10-second horizon price is near-random-walk; predictions are "
                "experimental and frequently do not beat a naive 'no change' baseline. "
                "Forecasts may lag sudden news events."
            ),
        }
    )


@require_GET
def provenance_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "data_provider": "Finnhub",
            "feed_delay_seconds": 1,
            "exchange_timezone": "America/New_York",
            "stale_after_seconds": 5,
        }
    )


@require_GET
def version_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "application_version": "0.1.0",
            "api_version": "v1",
            "build_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
