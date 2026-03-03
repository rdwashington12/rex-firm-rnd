#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "[warn] .env missing; created from .env.example. Update secrets before using in production."
fi

mkdir -p /var/data || true

docker compose up -d --build

echo "Deployment complete. Dashboard: http://<vm-ip>:8080"
echo "Prometheus (localhost only): http://127.0.0.1:9090"
echo "Grafana (localhost only): http://127.0.0.1:3000"
