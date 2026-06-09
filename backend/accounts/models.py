"""Per-user models: watchlist and search history."""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")
    ticker = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "ticker")
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - admin convenience
        return f"{self.user.username}:{self.ticker}"


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="searches")
    query = models.CharField(max_length=64)
    ticker = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - admin convenience
        return f"{self.user.username}:{self.query}"
