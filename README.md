# Alpaca Options Paper Trading System (Render-Friendly)

This project provides a paper-options trading system with three engines (Tactical Earnings, Drift, Wheel), a risk governor, and a dashboard.

## Render-first architecture (minimal ops)

- **Single Render Web Service** runs both processes in one container:
  - Bot API (localhost:8000)
  - Dashboard UI (public Render port)
- **SQLite** persistence in paper mode (`DATABASE_URL=sqlite:////var/data/trading.db`)
- Background bot cycle loop runs continuously in bot service lifespan.

## Required environment variables

- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `DASHBOARD_ADMIN_TOKEN`
- `DISCORD_WEBHOOK_URL` (optional)

Optional tuning:
- `DATABASE_URL` (default `sqlite:////var/data/trading.db`)
- `CYCLE_INTERVAL_SECONDS` (default `300`)
- `BOT_URL` (default `http://127.0.0.1:8000`)

## Deploy on Render

### Option A: Blueprint (`render.yaml`)

1. Push repository to GitHub.
2. In Render, create new **Blueprint** and select this repo.
3. Add secret env vars:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `DASHBOARD_ADMIN_TOKEN`
   - optional `DISCORD_WEBHOOK_URL`
4. Attach Render Disk at `/var/data` (configured in blueprint).
5. Deploy.

### Option B: Manual Web Service

- Environment: Docker
- Dockerfile: `trading_system/Dockerfile.dashboard`
- Start command: `/app/start_render.sh`
- Health check path: `/health`
- Add the same env vars as above.
- Add persistent disk mounted at `/var/data`.

## UptimeRobot

Use the dashboard public health endpoint for pings:

- `GET /health`

## Local run

```bash
cp .env.example .env
docker compose up -d --build
```

Dashboard: `http://localhost:8080`

## Security controls

- Dashboard login requires `DASHBOARD_ADMIN_TOKEN`.
- Bot control endpoints require bearer token.
- Risk controls include kill switch, risk modes, whitelist/blacklist, and audit logging.
