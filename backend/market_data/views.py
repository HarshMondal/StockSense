"""REST endpoints for symbol search and market snapshots."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Tuple

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from accounts.decorators import json_login_required

from .catalog import search_catalog
from .services import FinnhubClient, MarketHours, make_source

LOGGER = logging.getLogger(__name__)

# Simple process-wide TTL cache for search results (respect Finnhub rate limits).
_SEARCH_TTL = 600  # seconds
_search_cache: Dict[str, Tuple[float, list]] = {}


async def _search(query: str) -> list:
    client = FinnhubClient()
    try:
        return await client.search(query)
    finally:
        await client.aclose()


@json_login_required
@require_GET
def search_view(request: HttpRequest) -> JsonResponse:
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"results": []})

    key = query.lower()
    now = time.monotonic()
    cached = _search_cache.get(key)
    if cached and now - cached[0] < _SEARCH_TTL:
        return JsonResponse({"results": cached[1]})

    source = "finnhub"
    try:
        results = asyncio.run(_search(query))
        # Finnhub can return an empty list for valid-but-uncommon queries; fall
        # back to the catalog so the user always sees the obvious tickers.
        if not results:
            results, source = search_catalog(query), "catalog"
    except RuntimeError:
        # No API key configured -> degrade to the built-in catalog (keyless demo).
        results, source = search_catalog(query), "catalog"
    except Exception as exc:  # network / upstream failure -> still usable
        LOGGER.warning("Finnhub search failed for %r: %s; using catalog", query, exc)
        results, source = search_catalog(query), "catalog"

    _search_cache[key] = (now, results)
    return JsonResponse({"results": results, "source": source})


@json_login_required
@require_GET
def snapshot_view(request: HttpRequest, ticker: str) -> JsonResponse:
    ticker = ticker.upper()
    source = make_source()
    try:
        quote = asyncio.run(source.get_quote(ticker))
    except RuntimeError as exc:
        return JsonResponse({"detail": str(exc)}, status=503)
    except Exception as exc:  # pragma: no cover - upstream failure
        LOGGER.warning("Snapshot failed for %s: %s", ticker, exc)
        return JsonResponse({"detail": "Snapshot is temporarily unavailable."}, status=502)

    return JsonResponse(
        {
            "ticker": ticker,
            "price": quote.price,
            "volume": quote.volume,
            "timestamp": quote.timestamp.isoformat(),
            "source": source.name,
            "market_open": MarketHours.is_market_open(),
        }
    )
