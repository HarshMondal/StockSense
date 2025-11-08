"""RL engine application config."""
from django.apps import AppConfig


class RlEngineConfig(AppConfig):
    """Configuration for the rl_engine app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "rl_engine"
