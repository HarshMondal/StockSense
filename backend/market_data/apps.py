"""App configuration for market data."""
from django.apps import AppConfig


class MarketDataConfig(AppConfig):
    """Configuration for the market_data app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "market_data"
