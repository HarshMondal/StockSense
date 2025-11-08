# Stocksense

A dual-stack implementation of the Stocksense concept featuring a Django backend with Channels for streaming predictions and a React (Vite) frontend styled with shadcn/ui components. The system is designed to operate locally without containers, relying on `.env` configuration for secrets and runtime toggles.

## Project Structure

```
backend/
  manage.py              # Django entrypoint (ASGI ready)
  requirements.txt       # Python dependencies
  stocksense_backend/    # Settings, routing, ASGI configuration
  market_data/           # Finnhub clients and websocket consumers
  rl_engine/             # Online learning engine, services, trainer command
  analytics/             # Backtesting & baseline placeholder endpoints
  metadata/              # Model card, provenance, version metadata
frontend/
  package.json           # Vite + React + shadcn/ui dependencies
  vite.config.js         # Vite configuration
  src/                   # React application with modular feature folders
```

## Getting Started

### Backend

1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and populate values (Finnhub API key is required for live data):
   ```bash
   cp .env.example .env
   ```
3. Apply migrations and start the ASGI server:
   ```bash
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```
4. (Optional) Start the continual trainer loop in another terminal:
   ```bash
   python manage.py start_trainer --interval 60
   ```

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   npm run dev
   ```
2. Open the application at `http://localhost:5173`.

## Key Features

- **Online RL Engine:** `rl_engine.services.PredictionEngine` provides a light-weight continual learner that persists checkpoints to the filesystem for each ticker and horizon. The `start_trainer` management command pulls Finnhub quotes and updates policies at a configurable cadence.
- **Streaming Interfaces:** Channels-based consumers expose real-time market ticks (`ws/stream/<symbol>/`) and prediction updates (`ws/predictions/<symbol>/<horizon>/`).
- **API Surface:** REST endpoints under `/api/` support snapshots, backtesting placeholders, baseline metrics, and transparency metadata.
- **Shadcn-powered Frontend:** Modular React components deliver the dashboard layout, prediction intelligence, scenario simulator, watchlist management, and backtesting views. WebSocket hooks manage live updates and URL/state integration points for future enhancements.

## Next Steps

- Replace placeholder analytics with full statistical calculations and integrate charting library (e.g., `lightweight-charts`).
- Expand accessibility (keyboard shortcuts, narration) and strict privacy features (in-memory session mode toggle).
- Harden trainer loop with replay buffers, GPU-aware model implementations, and Finnhub rate-limit backoff strategies.

