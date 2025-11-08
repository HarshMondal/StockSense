"""Analytics HTTP views."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from rl_engine.services import ENGINE


@dataclass
class BacktestResult:
    ticker: str
    horizon: str
    cagr: float
    sharpe: float
    max_drawdown: float

    def as_dict(self) -> Dict[str, float | str]:
        return {
            "ticker": self.ticker,
            "horizon": self.horizon,
            "cagr": self.cagr,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
        }


@require_POST
def backtest_view(request) -> JsonResponse:
    payload = json.loads(request.body or "{}")
    ticker = payload.get("ticker", "AAPL")
    horizon = payload.get("horizon", "intraday")
    result = BacktestResult(
        ticker=ticker,
        horizon=horizon,
        cagr=0.12,
        sharpe=1.5,
        max_drawdown=-0.08,
    )
    return JsonResponse({"result": result.as_dict(), "generated_at": datetime.utcnow().isoformat()})


@require_POST
def baselines_view(request) -> JsonResponse:
    payload = json.loads(request.body or "{}")
    ticker = payload.get("ticker", "AAPL")
    horizon = payload.get("horizon", "intraday")
    baselines = [
        {"name": "naive", "cagr": 0.05, "sharpe": 0.9},
        {"name": "moving_average", "cagr": 0.08, "sharpe": 1.1},
        {"name": "momentum", "cagr": 0.1, "sharpe": 1.2},
    ]
    return JsonResponse(
        {
            "ticker": ticker,
            "horizon": horizon,
            "baselines": baselines,
        }
    )


@require_POST
def scenario_view(request) -> JsonResponse:
    payload = json.loads(request.body or "{}")
    ticker = payload.get("ticker", "AAPL")
    horizon = payload.get("horizon", "intraday")
    adjustments = payload.get("adjustments", {})
    features = [adjustments.get("next_open_pct", 0.0), adjustments.get("vix", 0.0), adjustments.get("volume_spike", 0.0)]
    prediction = ENGINE.predict(ticker, horizon, features or [1.0, 0.5, 0.25])
    return JsonResponse({"prediction": prediction.as_dict(), "adjustments": adjustments})
