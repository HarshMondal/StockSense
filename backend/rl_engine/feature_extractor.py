"""Feature extraction from market data for ML predictions."""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Iterable, Optional

from market_data.services import Quote

LOGGER = logging.getLogger(__name__)


@dataclass
class FeatureExtractor:
    """Extracts features from market quotes for ML predictions."""

    price_history: Deque[float] = None
    max_history: int = 100

    def __post_init__(self) -> None:
        """Initialize price history deque."""
        if self.price_history is None:
            self.price_history = deque(maxlen=self.max_history)

    def extract_features(self, quote: Quote, previous_quote: Optional[Quote] = None) -> list[float]:
        """
        Extract feature vector from a Quote object.
        
        Returns 3 features compatible with existing OnlinePolicy:
        1. Normalized price (using recent price history)
        2. Normalized volume/price ratio (if available)
        3. Price change percentage (momentum indicator)
        """
        # Update price history
        self.price_history.append(quote.price)
        
        # Feature 1: Normalized price (using recent average)
        if len(self.price_history) > 1:
            avg_price = sum(self.price_history) / len(self.price_history)
            normalized_price = quote.price / avg_price if avg_price > 0 else 1.0
        else:
            normalized_price = 1.0
        
        # Feature 2: Normalized volume/price ratio
        if quote.volume is not None and quote.price > 0:
            volume_ratio = quote.volume / quote.price
            # Normalize to 0-1 range (assuming typical volume/price ratios)
            normalized_volume = min(1.0, volume_ratio / 10000.0) if volume_ratio > 0 else 0.0
        else:
            normalized_volume = 0.5  # Default when volume not available
        
        # Feature 3: Price change percentage (momentum)
        if previous_quote and previous_quote.price > 0:
            price_change_pct = ((quote.price - previous_quote.price) / previous_quote.price)
            # Normalize to -1 to 1 range (clamp large changes)
            normalized_change = max(-1.0, min(1.0, price_change_pct * 10.0))
        else:
            normalized_change = 0.0
        
        return [normalized_price, normalized_volume, normalized_change]

    def extract_simple_features(self, quote: Quote) -> list[float]:
        """
        Extract simple feature vector (fallback when no history).
        Compatible with existing code that expects 3 features.
        """
        self.price_history.append(quote.price)
        
        # Simple features: price, normalized price, volume ratio
        price = quote.price
        normalized_price = price / 100.0 if price > 0 else 1.0  # Rough normalization
        volume_ratio = (quote.volume / price) if (quote.volume and price > 0) else 0.5
        
        return [normalized_price, min(1.0, volume_ratio / 1000.0), 0.0]

