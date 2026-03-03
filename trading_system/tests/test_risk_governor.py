from datetime import datetime, timezone, timedelta

from app.core.config import RiskLimits
from app.domain.models import ControlState, EngineName, TradeIdea, TradingState
from app.services.risk_governor import RiskGovernor


def test_rejects_over_trade_risk_limit() -> None:
    governor = RiskGovernor(RiskLimits())
    idea = TradeIdea(
        engine=EngineName.DRIFT,
        symbol="MSFT",
        strategy="call",
        notional_risk=0.02,
        horizon_days=5,
    )
    state = TradingState()
    control = ControlState()

    decision = governor.evaluate(idea, state, control)

    assert decision.approved is False


def test_wheel_blackout_logic() -> None:
    governor = RiskGovernor(RiskLimits())
    now = datetime.now(timezone.utc)
    idea = TradeIdea(
        engine=EngineName.WHEEL,
        symbol="KO",
        strategy="cash_secured_put",
        notional_risk=0.005,
        horizon_days=12,
    )
    state = TradingState(date=now, earnings_calendar={"KO": now + timedelta(days=5)})

    decision = governor.evaluate(idea, state, ControlState())

    assert decision.approved is False
    assert "blackout" in decision.reason.lower()
