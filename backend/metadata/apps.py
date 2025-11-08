"""Metadata configuration."""
from django.apps import AppConfig


class MetadataConfig(AppConfig):
    """Configuration for metadata app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "metadata"
