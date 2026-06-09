#!/usr/bin/env bash
set -e

echo "Applying migrations…"
python manage.py migrate --noinput

echo "Healing any diverged checkpoints…"
python manage.py reset_checkpoints || true

echo "Starting ASGI server on :8000…"
exec uvicorn stocksense_backend.asgi:application --host 0.0.0.0 --port 8000
