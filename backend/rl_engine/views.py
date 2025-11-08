"""HTTP views for RL predictions."""
from __future__ import annotations

import json
from typing import Dict, Iterable

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from stocksense_backend.settings.base import PREDICTION_HORIZONS

from .services import ENGINE


@require_http_methods(["GET", "POST"])
def prediction_snapshot_view(request, ticker: str, horizon: str) -> JsonResponse:
    """Return a snapshot of the latest prediction."""
    if horizon not in PREDICTION_HORIZONS:
        return JsonResponse({"error": "unsupported_horizon"}, status=400)

    features = _extract_features_from_request(request)
    prediction = ENGINE.predict(ticker, horizon, features)
    payload = prediction.as_dict()
    payload["source"] = "rl_engine"
    return JsonResponse(payload)


def _extract_features_from_request(request) -> Iterable[float]:
    body: Dict[str, object]
    if request.body:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            body = {}
    else:
        body = {}
    features = body.get("features") if isinstance(body, dict) else None
    if isinstance(features, list) and all(isinstance(item, (int, float)) for item in features):
        return [float(item) for item in features]
    # default feature vector fallback when none provided
    return [1.0, 0.5, 0.25]
