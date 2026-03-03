#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-10000}"
BOT_PORT="${BOT_PORT:-8000}"

uvicorn app.main:app --host 127.0.0.1 --port "$BOT_PORT" &
BOT_PID=$!

cleanup() {
  kill "$BOT_PID" 2>/dev/null || true
}
trap cleanup EXIT

exec uvicorn dashboard.main:app --host 0.0.0.0 --port "$PORT"
