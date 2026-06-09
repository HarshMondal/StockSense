"""Built-in symbol catalog used as a search fallback.

Finnhub's /search requires an API key and network access. To keep the app fully
demoable keyless/offline (search is the first thing a user does), we fall back to
filtering this small catalog of well-known US tickers.
"""
from __future__ import annotations

from typing import List

SYMBOL_CATALOG: List[dict] = [
    {"symbol": "AAPL", "description": "Apple Inc"},
    {"symbol": "MSFT", "description": "Microsoft Corp"},
    {"symbol": "GOOG", "description": "Alphabet Inc (Class C)"},
    {"symbol": "GOOGL", "description": "Alphabet Inc (Class A)"},
    {"symbol": "AMZN", "description": "Amazon.com Inc"},
    {"symbol": "NVDA", "description": "NVIDIA Corp"},
    {"symbol": "META", "description": "Meta Platforms Inc"},
    {"symbol": "TSLA", "description": "Tesla Inc"},
    {"symbol": "NFLX", "description": "Netflix Inc"},
    {"symbol": "AMD", "description": "Advanced Micro Devices Inc"},
    {"symbol": "INTC", "description": "Intel Corp"},
    {"symbol": "IBM", "description": "International Business Machines Corp"},
    {"symbol": "ORCL", "description": "Oracle Corp"},
    {"symbol": "CRM", "description": "Salesforce Inc"},
    {"symbol": "ADBE", "description": "Adobe Inc"},
    {"symbol": "PYPL", "description": "PayPal Holdings Inc"},
    {"symbol": "UBER", "description": "Uber Technologies Inc"},
    {"symbol": "DIS", "description": "Walt Disney Co"},
    {"symbol": "BA", "description": "Boeing Co"},
    {"symbol": "JPM", "description": "JPMorgan Chase & Co"},
    {"symbol": "V", "description": "Visa Inc"},
    {"symbol": "MA", "description": "Mastercard Inc"},
    {"symbol": "WMT", "description": "Walmart Inc"},
    {"symbol": "KO", "description": "Coca-Cola Co"},
    {"symbol": "PEP", "description": "PepsiCo Inc"},
    {"symbol": "NKE", "description": "Nike Inc"},
    {"symbol": "T", "description": "AT&T Inc"},
    {"symbol": "F", "description": "Ford Motor Co"},
    {"symbol": "GM", "description": "General Motors Co"},
    {"symbol": "SPY", "description": "SPDR S&P 500 ETF Trust"},
    {"symbol": "QQQ", "description": "Invesco QQQ Trust"},
]


def search_catalog(query: str, limit: int = 15) -> List[dict]:
    """Case-insensitive match on symbol or description."""
    q = query.strip().lower()
    if not q:
        return []
    results = [
        {**item, "type": "Common Stock", "displaySymbol": item["symbol"]}
        for item in SYMBOL_CATALOG
        if q in item["symbol"].lower() or q in item["description"].lower()
    ]
    # Prefer symbol-prefix matches first.
    results.sort(key=lambda r: (not r["symbol"].lower().startswith(q), r["symbol"]))
    return results[:limit]
