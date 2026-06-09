# StockSense

[![CI](https://github.com/OWNER/StockSense/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

**A real-time ML serving pipeline with online learning, live evaluation against baselines, and drift monitoring** — wrapped in a stock dashboard.

You log in, search a ticker, and watch a live price chart with a **second line** showing the model's prediction of where price will be **10 seconds ahead**. Every 10 seconds the model predicts, then observes the actual move, scores itself, and **updates its own weights** — and an honest scoreboard shows whether it actually beats naive baselines (often it doesn't, and that's the point).

> **On honesty:** at a 10-second horizon, price is essentially a random walk. This project is **not** a profitable trading signal and does not pretend to be. Its value is the engineering — streaming, online learning, and rigorous self-evaluation — and the discipline of measuring the model against baselines instead of showing a prediction line that merely *looks* right.

---

## Architecture

```
   React SPA (Vite/TS/Tailwind, :5173)
        │  REST (fetch, credentials: include + CSRF)        WebSocket
        │                                                   ws/predictions/<ticker>/<horizon>/
        ▼                                                          ▲
   ┌─────────────────────────  Django ASGI (:8000)  ─────────────────────────┐
   │  accounts (session auth)    market_data (REST: search, snapshot)         │
   │  rl_engine (REST: accuracy/history)    PredictionConsumer (thin relay)   │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                       │ Channels group  (Redis or in-memory)
                                       ▼
              PredictionLoopManager  —  ONE asyncio loop per (ticker, horizon)
                ├─ MarketDataSource ──▶ FinnhubLiveSource │ ReplaySimulatorSource ─▶ PriceCache
                ├─ FeatureExtractor (price / volume / momentum → 3 features)
                └─ OnlinePolicy.predict()/update()  ─▶  checkpoints/<T>/<H>.json + PredictionLog
```

**Why one loop per (ticker, horizon)?** It owns the single policy and is the *sole writer* of its checkpoint, so N browsers watching the same ticker can't cause training races or double-counted updates. Loops are reference-counted and keep learning even with no browser attached.

---

## Quick start

### One command (Docker)

```bash
cp .env.example .env          # optional: add your free FINNHUB_API_KEY
docker compose up --build
```

Then open **http://localhost:5173**. The stack runs backend + frontend + Redis. It defaults to `STOCKSENSE_FORCE_REPLAY=1` so the live 10-second loop is demoable **even when the US market is closed** (it replays a seeded random walk). Set it to `0` to use the live Finnhub feed during market hours.

### Manual (dev)

```bash
# Backend
cd backend
uv venv && uv pip install -r requirements.txt   # or: python -m venv .venv && pip install -r requirements.txt
python manage.py migrate
python manage.py reset_checkpoints               # heal the seeded diverged checkpoints
DJANGO_SETTINGS_MODULE=stocksense_backend.settings.dev \
  uvicorn stocksense_backend.asgi:application --reload --port 8000

# Frontend (new shell)
cd frontend
npm install
npm run dev                                       # http://localhost:5173
```

---

## How the prediction + learning loop works

Every 10 seconds, for each watched `(ticker, horizon)`:

1. **Sample** the latest price from `PriceCache` (kept fresh by a single websocket / simulator stream — the sampler never makes a per-tick REST call, so we stay under Finnhub's free-tier rate limit).
2. **Resolve** the prediction made 10s ago: compute the actual return, score the model **and** two baselines (naive "no change" + random-walk), call `OnlinePolicy.update()`, and persist a `PredictionLog` row.
3. **Predict** the next 10-second return, broadcast both lines to the browser, and (debounced) save the checkpoint.

### The numerically stable `OnlinePolicy`

The seeded checkpoints in this repo are *diverged* (weights ≈ 1e17) — a deliberate artifact of the original naive design, which regressed **raw dollar prices** with unbounded SGD. The fix:

- predict a **bounded fractional return** (`±5%`), never a raw price;
- normalize features to `O(1)`, **clip the gradient** norm, apply weight decay;
- guard against NaN/inf and **auto-heal** any diverged checkpoint on load.

A regression test feeds 10⁴ adversarial updates and asserts the weights stay finite and `< 10` — see `backend/rl_engine/tests/test_policy.py`.

---

## The scoreboard (the centerpiece)

`GET /api/predictions/<ticker>/<horizon>/accuracy/` returns the model vs. naive vs. random-walk:

```json
{ "count": 42,
  "model": { "rolling_mae": 0.0011, "directional_accuracy": 0.48, "update_count": 42 },
  "naive": { "mae": 0.00104, "directional_accuracy": null },
  "random_walk": { "mae": 0.00105 },
  "beats_naive": false }
```

The dashboard surfaces this as a big "beats baseline?" badge, a MAE comparison, directional accuracy, and a MAE-trend sparkline.

---

## API overview

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/auth/csrf/` | seed CSRF cookie |
| POST | `/api/auth/{signup,login,logout}/` · GET `/api/auth/me/` | session auth |
| GET | `/api/search/?q=` | symbol autocomplete (Finnhub) |
| GET | `/api/market/<ticker>/snapshot/` | latest quote |
| WS | `/ws/predictions/<ticker>/<horizon>/` | live dual-line stream (10s cadence) |
| GET | `/api/predictions/<ticker>/<horizon>/{accuracy,history,snapshot}/` | scoreboard + history |
| GET | `/api/meta/{model-card,provenance,version}/` | model card / provenance |

Horizons: `intraday`, `daily`, `weekly`.

---

## Testing

```bash
cd backend && make test     # clears PYTHONPATH, runs pytest
```

Covers the `OnlinePolicy` stability guarantee, baseline-scoring helpers, and the auth flow. CI (`.github/workflows/ci.yml`) runs the backend tests and the frontend build on every push.

---

## Tech stack

**Backend:** Django 5.2 + Channels (ASGI/WebSockets), httpx, NumPy, Redis channel layer (in-memory fallback), SQLite.
**Frontend:** React 18 + TypeScript + Vite + Tailwind + Radix UI + SWR + lightweight-charts.
**Data:** Finnhub free tier, with a built-in replay simulator for out-of-hours demos.

## Project structure

```
backend/
  accounts/        session auth (signup/login/logout/me) + watchlist models
  market_data/     Quote, FinnhubClient, live + replay sources, PriceCache, MarketHours
  rl_engine/       OnlinePolicy, PredictionEngine, PredictionLoopManager, consumer, scoreboard
  metadata/        model card / provenance / version
  stocksense_backend/  settings (split base/dev), asgi (ProtocolTypeRouter), urls
frontend/          Vite/React SPA (auth, search, dashboard, evaluation panel)
docker-compose.yml one-command stack (backend + frontend + redis)
```

> _Demo GIF placeholder:_ record the dashboard (search → dual-line chart + evaluation panel) and drop it here as `docs/demo.gif`.
