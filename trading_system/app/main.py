import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, Header
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.schemas import ControlUpdate
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.domain.models import ControlState
from app.services.alerts import DiscordAlerter
from app.services.alpaca_client import AlpacaPaperClient
from app.services.auth import require_bearer_token
from app.services.db import Database
from app.services.metrics import ENGINE_ENABLED, KILL_SWITCH, RISK_MODE
from app.services.orchestrator import TradingOrchestrator
from app.services.persistence import TradingRepository
from app.services.risk_governor import RiskGovernor
from app.services.state_store import InMemoryStateStore

settings = get_settings()
configure_logging()
LOGGER = logging.getLogger(__name__)

db = Database(settings.database_url)
repository = TradingRepository(db)
state_store = InMemoryStateStore()
risk_governor = RiskGovernor(settings.risk_limits)
broker = AlpacaPaperClient(
    settings.alpaca_api_key.get_secret_value(),
    settings.alpaca_secret_key.get_secret_value(),
    settings.alpaca_base_url,
    timeout_seconds=settings.request_timeout_seconds,
    max_retries=settings.max_retries,
)
alerter = DiscordAlerter(
    settings.discord_webhook_url.get_secret_value() if settings.discord_webhook_url else None
)
orchestrator = TradingOrchestrator(state_store, risk_governor, broker, alerter, repository)


def enforce_auth(authorization: str | None = Header(default=None)) -> None:
    require_bearer_token(authorization, settings.dashboard_admin_token.get_secret_value())


async def cycle_loop() -> None:
    while True:
        try:
            result = await orchestrator.run_cycle()
            LOGGER.info("cycle_loop_executed", extra={"result": result})
        except Exception as exc:  # keep service alive
            LOGGER.exception("cycle_loop_failed", extra={"error": str(exc)})
        await asyncio.sleep(settings.cycle_interval_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.migrate()
    await orchestrator.reconcile()
    control = orchestrator.get_controls()
    ENGINE_ENABLED.labels(engine="tactical_earnings").set(1 if control.tactical_earnings_enabled else 0)
    ENGINE_ENABLED.labels(engine="drift").set(1 if control.drift_enabled else 0)
    ENGINE_ENABLED.labels(engine="wheel").set(1 if control.wheel_enabled else 0)
    KILL_SWITCH.set(1 if control.kill_switch else 0)
    RISK_MODE.set({"normal": 0, "reduce": 1, "flat": 2}[control.risk_mode])

    loop_task = asyncio.create_task(cycle_loop())
    yield
    loop_task.cancel()
    with suppress(asyncio.CancelledError):
        await loop_task


app = FastAPI(title="Trading Bot", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "bot"}


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.post("/run-cycle", dependencies=[Depends(enforce_auth)])
async def run_cycle() -> dict[str, int]:
    return await orchestrator.run_cycle()


@app.post("/reconcile", dependencies=[Depends(enforce_auth)])
async def reconcile() -> dict[str, int]:
    return await orchestrator.reconcile()


@app.get("/controls", dependencies=[Depends(enforce_auth)])
async def get_controls() -> ControlState:
    return orchestrator.get_controls()


@app.post("/controls", dependencies=[Depends(enforce_auth)])
async def set_controls(update: ControlUpdate) -> ControlState:
    control = ControlState(**update.model_dump())
    ENGINE_ENABLED.labels(engine="tactical_earnings").set(1 if control.tactical_earnings_enabled else 0)
    ENGINE_ENABLED.labels(engine="drift").set(1 if control.drift_enabled else 0)
    ENGINE_ENABLED.labels(engine="wheel").set(1 if control.wheel_enabled else 0)
    KILL_SWITCH.set(1 if control.kill_switch else 0)
    RISK_MODE.set({"normal": 0, "reduce": 1, "flat": 2}[control.risk_mode])
    return orchestrator.set_controls(control)


@app.get("/audit", dependencies=[Depends(enforce_auth)])
async def audit() -> list[dict[str, str]]:
    records = repository.recent_audit()
    return [
        {
            "actor": r.actor,
            "action": r.action,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]
