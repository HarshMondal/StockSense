"""Per-(ticker, horizon) prediction loop — the single source of truth.

One asyncio sampler task per (ticker, horizon) owns the single OnlinePolicy and
is the SOLE writer of its checkpoint, so N browser connections to the same ticker
never cause training races or double-counted updates. A per-ticker stream drainer
keeps PRICE_CACHE fresh. Tasks are reference-counted and stop (debounced) after the
last subscriber leaves; they keep learning even with no browser attached.

Each 10s tick:
  1. read the latest price from PRICE_CACHE
  2. resolve the prediction made 10s ago -> score model + naive + random-walk
     baselines, run policy.update(), persist the PredictionLog row
  3. emit a fresh prediction for t+10s and broadcast it to the group
"""
from __future__ import annotations

import asyncio
import logging
import math
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Optional, Tuple

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

from market_data.services import Quote, make_source
from .feature_extractor import FeatureExtractor
from .services import ENGINE

LOGGER = logging.getLogger(__name__)

TICK_SECONDS = 10
LOOKAHEAD_SECONDS = 10          # predict where price will be 10s ahead
STOP_DEBOUNCE_SECONDS = 30      # keep loop warm briefly after last unsubscribe
SAVE_EVERY_UPDATES = 5          # debounce checkpoint writes
_EPS = 1e-9


def group_name(ticker: str, horizon: str) -> str:
    return f"pred.{ticker.upper()}.{horizon}"


@dataclass
class _Pending:
    target_at: datetime
    base_price: float
    features: list
    predicted_return: float
    predicted_price: float
    naive_return: float
    rw_return: float
    rw_sigma: float
    log_id: Optional[int] = None


@dataclass
class _SamplerState:
    ticker: str
    horizon: str
    refcount: int = 0
    task: Optional[asyncio.Task] = None
    stop_handle: Optional[asyncio.TimerHandle] = None


class PredictionLoopManager:
    """Supervises stream drainers (per ticker) and samplers (per ticker/horizon)."""

    def __init__(self) -> None:
        self._samplers: Dict[Tuple[str, str], _SamplerState] = {}
        self._stream_refs: Dict[str, int] = {}
        self._stream_tasks: Dict[str, asyncio.Task] = {}
        self._source = None

    def _get_source(self):
        if self._source is None:
            self._source = make_source()
        return self._source

    # -- lifecycle ------------------------------------------------------- #
    async def acquire(self, ticker: str, horizon: str) -> None:
        ticker = ticker.upper()
        self._ensure_stream(ticker)
        key = (ticker, horizon)
        state = self._samplers.get(key)
        if state is None:
            state = _SamplerState(ticker=ticker, horizon=horizon)
            self._samplers[key] = state
        state.refcount += 1
        if state.stop_handle is not None:
            state.stop_handle.cancel()
            state.stop_handle = None
        if state.task is None or state.task.done():
            state.task = asyncio.create_task(self._run_sampler(ticker, horizon))
            LOGGER.info("Started prediction loop for %s/%s", ticker, horizon)

    async def release(self, ticker: str, horizon: str) -> None:
        ticker = ticker.upper()
        key = (ticker, horizon)
        state = self._samplers.get(key)
        if state is None:
            return
        state.refcount = max(0, state.refcount - 1)
        if state.refcount == 0 and state.stop_handle is None:
            loop = asyncio.get_running_loop()
            state.stop_handle = loop.call_later(
                STOP_DEBOUNCE_SECONDS, lambda: asyncio.create_task(self._stop(key))
            )

    async def _stop(self, key: Tuple[str, str]) -> None:
        state = self._samplers.get(key)
        if state is None or state.refcount > 0:
            return
        if state.task is not None:
            state.task.cancel()
        self._samplers.pop(key, None)
        self._release_stream(key[0])
        LOGGER.info("Stopped prediction loop for %s/%s", *key)

    def _ensure_stream(self, ticker: str) -> None:
        self._stream_refs[ticker] = self._stream_refs.get(ticker, 0) + 1
        if ticker not in self._stream_tasks or self._stream_tasks[ticker].done():
            self._stream_tasks[ticker] = asyncio.create_task(self._drain_stream(ticker))

    def _release_stream(self, ticker: str) -> None:
        self._stream_refs[ticker] = max(0, self._stream_refs.get(ticker, 0) - 1)
        if self._stream_refs[ticker] == 0:
            task = self._stream_tasks.pop(ticker, None)
            if task is not None:
                task.cancel()

    # -- workers --------------------------------------------------------- #
    async def _drain_stream(self, ticker: str) -> None:
        """Pump the source stream so PRICE_CACHE stays fresh for the sampler."""
        source = self._get_source()
        try:
            async for _quote in source.stream(ticker):
                pass  # stream writes PRICE_CACHE as a side effect
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - resilience
            LOGGER.warning("Stream drainer error for %s: %s", ticker, exc)

    async def _run_sampler(self, ticker: str, horizon: str) -> None:
        source = self._get_source()
        policy = ENGINE.load_policy(ticker, horizon)
        extractor = FeatureExtractor()
        channel_layer = get_channel_layer()

        prev_quote: Optional[Quote] = None
        pending: Optional[_Pending] = None
        returns: Deque[float] = deque(maxlen=50)
        rolling_mae: Optional[float] = None
        updates_since_save = 0
        last_resolved: Optional[dict] = None
        rng = random.Random(hash((ticker, horizon)) & 0xFFFFFFFF)

        try:
            # Seed the cache so the first tick has a price even before the stream warms up.
            await source.get_quote(ticker)
            while True:
                now = datetime.now(timezone.utc)
                quote = await self._current_quote(source, ticker)
                if quote is None:
                    await asyncio.sleep(TICK_SECONDS)
                    continue

                # 1) Resolve the previous prediction (its target is ~now).
                if pending is not None and pending.target_at <= now + timedelta(seconds=0.5):
                    actual_return = (quote.price - pending.base_price) / pending.base_price \
                        if pending.base_price else 0.0
                    returns.append(actual_return)

                    error = pending.predicted_return - actual_return
                    abs_error = abs(error)
                    hit = _same_sign(pending.predicted_return, actual_return)
                    naive_abs = abs(pending.naive_return - actual_return)
                    naive_hit = abs(actual_return) < 1e-6
                    rw_abs = abs(pending.rw_return - actual_return)

                    policy.update(pending.features, actual_return)
                    updates_since_save += 1
                    rolling_mae = abs_error if rolling_mae is None \
                        else 0.2 * abs_error + 0.8 * rolling_mae

                    await self._resolve_log(
                        pending.log_id, quote.price, actual_return, error, abs_error,
                        hit, naive_abs, naive_hit, rw_abs,
                    )
                    await self._save_meta(ticker, horizon, updates_since_save, rolling_mae,
                                          policy.learning_rate)
                    if updates_since_save >= SAVE_EVERY_UPDATES:
                        await sync_to_async(ENGINE.save_policy)(policy)
                        updates_since_save = 0

                    last_resolved = {
                        "predicted_price": pending.predicted_price,
                        "actual_price": quote.price,
                        "error": error,
                        "abs_error": abs_error,
                        "hit": hit,
                        "naive_abs_error": naive_abs,
                        "target_at": pending.target_at.isoformat(),
                    }
                    pending = None

                # 2) Emit a fresh prediction for t + LOOKAHEAD.
                features = extractor.extract_features(quote, prev_quote)
                r_hat = policy.predict(features)
                predicted_price = quote.price * (1.0 + r_hat)
                sigma = _stddev(returns)
                rw_return = rng.gauss(0.0, sigma) if sigma > 0 else 0.0
                target_at = now + timedelta(seconds=LOOKAHEAD_SECONDS)

                log_id = await self._create_log(
                    ticker, horizon, now, target_at, quote.price, r_hat,
                    predicted_price, naive_return=0.0, rw_sigma=sigma, source=source.name,
                )
                pending = _Pending(
                    target_at=target_at, base_price=quote.price, features=list(features),
                    predicted_return=r_hat, predicted_price=predicted_price,
                    naive_return=0.0, rw_return=rw_return, rw_sigma=sigma, log_id=log_id,
                )

                # 3) Broadcast.
                payload = {
                    "type": "tick",
                    "ticker": ticker,
                    "horizon": horizon,
                    "timestamp": quote.timestamp.isoformat(),
                    "price": quote.price,
                    "predicted_price": predicted_price,
                    "predicted_return": r_hat,
                    "predicted_at": now.isoformat(),
                    "target_at": target_at.isoformat(),
                    "last_prediction": last_resolved,
                    "rolling_mae": rolling_mae,
                    "source": source.name,
                }
                await channel_layer.group_send(
                    group_name(ticker, horizon),
                    {"type": "prediction.tick", "payload": payload},
                )

                prev_quote = quote
                await asyncio.sleep(TICK_SECONDS)
        except asyncio.CancelledError:
            if updates_since_save:
                await sync_to_async(ENGINE.save_policy)(policy)
            raise
        except Exception as exc:  # pragma: no cover - keep the worker alive in logs
            LOGGER.exception("Sampler crashed for %s/%s: %s", ticker, horizon, exc)

    async def _current_quote(self, source, ticker: str) -> Optional[Quote]:
        from market_data.services import PRICE_CACHE

        quote = PRICE_CACHE.get(ticker)
        if quote is not None:
            return quote
        try:
            return await source.get_quote(ticker)
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("No quote available for %s: %s", ticker, exc)
            return None

    # -- ORM helpers (sync, wrapped) ------------------------------------- #
    @sync_to_async
    def _create_log(self, ticker, horizon, predicted_at, target_at, base_price,
                    predicted_return, predicted_price, naive_return, rw_sigma, source) -> int:
        from .models import PredictionLog

        row = PredictionLog.objects.create(
            ticker=ticker, horizon=horizon, predicted_at=predicted_at, target_at=target_at,
            base_price=base_price, predicted_return=predicted_return,
            predicted_price=predicted_price, naive_return=naive_return, rw_sigma=rw_sigma,
            source=source,
        )
        return row.id

    @sync_to_async
    def _resolve_log(self, log_id, actual_price, actual_return, error, abs_error, hit,
                     naive_abs, naive_hit, rw_abs) -> None:
        from .models import PredictionLog

        if log_id is None:
            return
        PredictionLog.objects.filter(id=log_id).update(
            actual_price=actual_price, actual_return=actual_return, error=error,
            abs_error=abs_error, hit=hit, naive_abs_error=naive_abs, naive_hit=naive_hit,
            rw_abs_error=rw_abs, resolved=True,
        )

    @sync_to_async
    def _save_meta(self, ticker, horizon, update_delta, rolling_mae, learning_rate) -> None:
        from .models import ModelCheckpointMeta

        meta, _ = ModelCheckpointMeta.objects.get_or_create(ticker=ticker, horizon=horizon)
        meta.update_count = (meta.update_count or 0) + 1
        meta.rolling_mae = rolling_mae
        meta.learning_rate = learning_rate
        meta.last_saved_at = datetime.now(timezone.utc)
        meta.save()


def _same_sign(a: float, b: float) -> bool:
    if abs(a) < _EPS or abs(b) < _EPS:
        return abs(a) < _EPS and abs(b) < _EPS
    return (a > 0) == (b > 0)


def _stddev(values) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(max(0.0, var))


# Module-level singleton.
LOOP_MANAGER = PredictionLoopManager()
