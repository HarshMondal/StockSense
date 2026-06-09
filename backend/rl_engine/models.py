"""Persistence for predictions and checkpoint metadata."""
from __future__ import annotations

from django.db import models


class PredictionLog(models.Model):
    """One model prediction for t+horizon, plus baseline references, scored on resolution."""

    ticker = models.CharField(max_length=16, db_index=True)
    horizon = models.CharField(max_length=16)

    predicted_at = models.DateTimeField(db_index=True)  # t
    target_at = models.DateTimeField()                  # t + horizon seconds
    base_price = models.FloatField()

    # Model prediction
    predicted_return = models.FloatField()
    predicted_price = models.FloatField()

    # Baselines (recorded at prediction time; scored at resolution time)
    naive_return = models.FloatField(default=0.0)        # persistence: price unchanged
    rw_sigma = models.FloatField(default=0.0)            # recent stddev used for random-walk

    # Resolution (filled when target_at elapses)
    actual_price = models.FloatField(null=True, blank=True)
    actual_return = models.FloatField(null=True, blank=True)
    error = models.FloatField(null=True, blank=True)
    abs_error = models.FloatField(null=True, blank=True)
    hit = models.BooleanField(null=True, blank=True)     # directional correctness

    naive_abs_error = models.FloatField(null=True, blank=True)
    naive_hit = models.BooleanField(null=True, blank=True)
    rw_abs_error = models.FloatField(null=True, blank=True)

    resolved = models.BooleanField(default=False, db_index=True)
    source = models.CharField(max_length=16, default="live")  # "live" | "replay"

    class Meta:
        indexes = [
            models.Index(fields=["ticker", "horizon", "predicted_at"]),
            models.Index(fields=["ticker", "horizon", "resolved"]),
        ]
        ordering = ["-predicted_at"]

    def __str__(self) -> str:  # pragma: no cover - admin convenience
        return f"{self.ticker}/{self.horizon}@{self.predicted_at:%H:%M:%S}"


class ModelCheckpointMeta(models.Model):
    """DB-queryable stats for an on-disk checkpoint (weights stay in JSON)."""

    ticker = models.CharField(max_length=16)
    horizon = models.CharField(max_length=16)
    update_count = models.PositiveIntegerField(default=0)
    last_saved_at = models.DateTimeField(null=True, blank=True)
    rolling_mae = models.FloatField(null=True, blank=True)
    learning_rate = models.FloatField(default=0.05)

    class Meta:
        unique_together = ("ticker", "horizon")

    def __str__(self) -> str:  # pragma: no cover - admin convenience
        return f"{self.ticker}/{self.horizon} (n={self.update_count})"
