"""REST endpoints for prediction history and the model-vs-baseline scoreboard."""
from __future__ import annotations

from django.db.models import Avg
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from accounts.decorators import json_login_required
from stocksense_backend.settings.base import PREDICTION_HORIZONS

from .models import ModelCheckpointMeta, PredictionLog


def _bad_horizon(horizon: str) -> JsonResponse | None:
    if horizon not in PREDICTION_HORIZONS:
        return JsonResponse({"detail": "unsupported_horizon"}, status=400)
    return None


@json_login_required
@require_GET
def prediction_snapshot_view(request: HttpRequest, ticker: str, horizon: str) -> JsonResponse:
    if (bad := _bad_horizon(horizon)) is not None:
        return bad
    row = (
        PredictionLog.objects.filter(ticker=ticker.upper(), horizon=horizon)
        .order_by("-predicted_at")
        .first()
    )
    if row is None:
        return JsonResponse({"ticker": ticker.upper(), "horizon": horizon, "prediction": None})
    return JsonResponse(
        {
            "ticker": ticker.upper(),
            "horizon": horizon,
            "prediction": {
                "predicted_at": row.predicted_at.isoformat(),
                "target_at": row.target_at.isoformat(),
                "base_price": row.base_price,
                "predicted_price": row.predicted_price,
                "predicted_return": row.predicted_return,
                "resolved": row.resolved,
            },
        }
    )


@json_login_required
@require_GET
def prediction_history_view(request: HttpRequest, ticker: str, horizon: str) -> JsonResponse:
    if (bad := _bad_horizon(horizon)) is not None:
        return bad
    try:
        limit = min(500, max(1, int(request.GET.get("limit", 100))))
    except ValueError:
        limit = 100
    rows = list(
        PredictionLog.objects.filter(ticker=ticker.upper(), horizon=horizon)
        .order_by("-predicted_at")[:limit]
    )
    rows.reverse()
    return JsonResponse(
        {
            "ticker": ticker.upper(),
            "horizon": horizon,
            "points": [
                {
                    "predicted_at": r.predicted_at.isoformat(),
                    "target_at": r.target_at.isoformat(),
                    "base_price": r.base_price,
                    "predicted_price": r.predicted_price,
                    "actual_price": r.actual_price,
                    "error": r.error,
                    "resolved": r.resolved,
                    "source": r.source,
                }
                for r in rows
            ],
        }
    )


def _directional_accuracy(qs, field: str = "hit") -> float | None:
    total = qs.filter(**{f"{field}__isnull": False}).count()
    if total == 0:
        return None
    hits = qs.filter(**{field: True}).count()
    return hits / total


@json_login_required
@require_GET
def accuracy_view(request: HttpRequest, ticker: str, horizon: str) -> JsonResponse:
    """The honest scoreboard: model vs naive vs random-walk."""
    if (bad := _bad_horizon(horizon)) is not None:
        return bad
    ticker = ticker.upper()
    resolved = PredictionLog.objects.filter(ticker=ticker, horizon=horizon, resolved=True)
    count = resolved.count()

    agg = resolved.aggregate(
        model_mae=Avg("abs_error"),
        naive_mae=Avg("naive_abs_error"),
        rw_mae=Avg("rw_abs_error"),
        mean_error=Avg("error"),
    )
    model_mae = agg["model_mae"]
    naive_mae = agg["naive_mae"]

    # MAE trend: last 30 resolved rows (chronological).
    recent = list(
        resolved.order_by("-predicted_at").values_list("abs_error", "predicted_at")[:30]
    )
    recent.reverse()
    mae_trend = [{"t": t.isoformat(), "abs_error": e} for e, t in recent if e is not None]

    meta = ModelCheckpointMeta.objects.filter(ticker=ticker, horizon=horizon).first()

    return JsonResponse(
        {
            "ticker": ticker,
            "horizon": horizon,
            "count": count,
            "model": {
                "rolling_mae": meta.rolling_mae if meta else None,
                "mae": model_mae,
                "directional_accuracy": _directional_accuracy(resolved),
                "mean_error": agg["mean_error"],
                "update_count": meta.update_count if meta else 0,
            },
            "naive": {
                "mae": naive_mae,
                "directional_accuracy": _directional_accuracy(resolved, "naive_hit"),
            },
            "random_walk": {"mae": agg["rw_mae"]},
            "mae_trend": mae_trend,
            "beats_naive": (
                model_mae is not None and naive_mae is not None and model_mae < naive_mae
            ),
        }
    )
