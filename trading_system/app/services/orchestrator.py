from __future__ import annotations

import logging
from uuid import uuid4

from app.domain.models import ControlState, TradeIdea
from app.engines.drift import DriftEngine
from app.engines.tactical_earnings import TacticalEarningsEngine
from app.engines.wheel import WheelEngine
from app.services.alerts import DiscordAlerter
from app.services.alpaca_client import AlpacaPaperClient
from app.services.metrics import TRADE_DECISIONS
from app.services.persistence import TradingRepository
from app.services.risk_governor import RiskGovernor
from app.services.state_store import InMemoryStateStore

LOGGER = logging.getLogger(__name__)


class TradingOrchestrator:
    def __init__(
        self,
        state_store: InMemoryStateStore,
        risk_governor: RiskGovernor,
        broker: AlpacaPaperClient,
        alerter: DiscordAlerter,
        repository: TradingRepository,
    ) -> None:
        self.state_store = state_store
        self.risk_governor = risk_governor
        self.broker = broker
        self.alerter = alerter
        self.repository = repository
        self.engines = {
            "tactical_earnings": TacticalEarningsEngine(),
            "drift": DriftEngine(),
            "wheel": WheelEngine(),
        }

    async def reconcile(self) -> dict[str, int]:
        open_orders = await self.broker.list_open_orders()
        for order in open_orders:
            client_order_id = str(order.get("client_order_id", ""))
            if client_order_id and not self.repository.get_by_client_order_id(client_order_id):
                self.repository.create_order(
                    client_order_id=client_order_id,
                    symbol=str(order.get("symbol", "UNKNOWN")),
                    engine="reconciled",
                    strategy="recovered",
                    payload=order,
                )
            self.repository.update_order_status(
                client_order_id=client_order_id,
                status=str(order.get("status", "open")),
                external_order_id=str(order.get("id", "")),
            )

        positions = await self.broker.list_positions()
        for position in positions:
            self.repository.upsert_position(
                symbol=str(position.get("symbol", "UNKNOWN")),
                qty=float(position.get("qty", 0)),
                avg_entry_price=float(position.get("avg_entry_price", 0)),
                market_value=float(position.get("market_value", 0)),
                side=str(position.get("side", "long")),
            )

        return {"open_orders": len(open_orders), "positions": len(positions)}

    async def run_cycle(self) -> dict[str, int]:
        control = self.state_store.get_control()
        state = self.state_store.get_trading()

        generated: list[TradeIdea] = []
        if control.tactical_earnings_enabled:
            generated.extend(self.engines["tactical_earnings"].generate(state))
        if control.drift_enabled:
            generated.extend(self.engines["drift"].generate(state))
        if control.wheel_enabled:
            generated.extend(self.engines["wheel"].generate(state))

        approved = 0
        rejected = 0
        for idea in generated:
            decision = self.risk_governor.evaluate(idea, state, control)
            TRADE_DECISIONS.labels(engine=idea.engine.value, approved=str(decision.approved).lower()).inc()
            if not decision.approved:
                rejected += 1
                LOGGER.info("trade_rejected", extra={"symbol": idea.symbol, "reason": decision.reason})
                await self.alerter.send(f"Trade rejected for {idea.symbol}: {decision.reason}")
                continue

            client_order_id = f"{idea.engine.value}-{idea.symbol}-{uuid4().hex[:12]}"
            if self.repository.get_by_client_order_id(client_order_id):
                LOGGER.info("trade_idempotent_skip", extra={"client_order_id": client_order_id})
                continue

            self.repository.create_order(
                client_order_id=client_order_id,
                symbol=idea.symbol,
                engine=idea.engine.value,
                strategy=idea.strategy,
                payload=idea.model_dump(),
            )

            response = await self.broker.submit_options_order(idea, client_order_id)
            external_order_id = str(response.get("id", ""))
            status = str(response.get("status", "accepted"))
            self.repository.update_order_status(client_order_id, status=status, external_order_id=external_order_id)

            if status in {"filled", "partially_filled"}:
                filled_avg_price = float(response.get("filled_avg_price", 0) or 0)
                filled_qty = float(response.get("filled_qty", 0) or 0)
                self.repository.add_fill(external_order_id, idea.symbol, filled_qty, filled_avg_price)

            approved += 1
            LOGGER.info(
                "trade_executed",
                extra={"client_order_id": client_order_id, "external_order_id": external_order_id, "symbol": idea.symbol},
            )

        return {"generated": len(generated), "approved": approved, "rejected": rejected}

    def set_controls(self, control: ControlState, actor: str = "dashboard") -> ControlState:
        updated = self.state_store.update_control(control)
        self.repository.add_control_audit(actor=actor, action="control_update", detail=control.model_dump())
        return updated

    def get_controls(self) -> ControlState:
        return self.state_store.get_control()
