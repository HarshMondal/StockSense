"""Metadata endpoints."""
from __future__ import annotations

from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def model_card_view(request) -> JsonResponse:
    return JsonResponse(
        {
            "model": {
                "name": "Stocksense Online RL",
                "version": "1.0.0",
                "last_retrain": datetime.utcnow().isoformat(),
                "horizons": ["intraday", "daily", "weekly"],
                "description": "Online learner adapting to Finnhub price movements in real time.",
                "known_risks": [
                    "Live market data can be noisy; forecasts are experimental.",
                    "Predictions adjust gradually and may lag sudden news events.",
                ],
            }
        }
    )


@require_GET
def provenance_view(request) -> JsonResponse:
    return JsonResponse(
        {
            "data_provider": "Finnhub",
            "feed_delay_seconds": 1,
            "exchange_timezone": "America/New_York",
            "stale_after_seconds": 5,
        }
    )


@require_GET
def version_view(request) -> JsonResponse:
    return JsonResponse(
        {
            "application_version": "0.1.0",
            "api_version": "v1",
            "build_timestamp": datetime.utcnow().isoformat(),
        }
    )
