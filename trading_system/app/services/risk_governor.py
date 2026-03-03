from __future__ import annotations

from datetime import timedelta

from app.core.config import RiskLimits
from app.domain.models import ControlState, EngineName, ExecutionDecision, TradeIdea, TradingState


class RiskGovernor:
    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits

    def evaluate(self, idea: TradeIdea, state: TradingState, control: ControlState) -> ExecutionDecision:
        if control.kill_switch or control.risk_mode == "flat":
            return ExecutionDecision(approved=False, reason="Kill switch or flat mode engaged")

        if idea.symbol in control.blacklist:
            return ExecutionDecision(approved=False, reason="Symbol is blacklisted")

        if control.whitelist and idea.symbol not in control.whitelist:
            return ExecutionDecision(approved=False, reason="Symbol outside whitelist")

        if state.day_pnl_pct <= -self.limits.max_daily_loss_pct:
            return ExecutionDecision(approved=False, reason="Daily loss limit reached")

        per_trade_cap = self.limits.risk_per_trade_pct
        if control.risk_mode == "reduce":
            per_trade_cap *= 0.5
        if idea.notional_risk > per_trade_cap:
            return ExecutionDecision(approved=False, reason="Risk per trade exceeds cap")

        if idea.engine == EngineName.TACTICAL_EARNINGS and (
            state.open_earnings_trades >= self.limits.max_concurrent_earnings
        ):
            return ExecutionDecision(approved=False, reason="Max concurrent earnings trades reached")

        if idea.engine == EngineName.WHEEL:
            if state.assignment_exposure_pct >= self.limits.assignment_exposure_cap_pct:
                return ExecutionDecision(approved=False, reason="Assignment exposure cap reached")
            earnings_dt = state.earnings_calendar.get(idea.symbol)
            if earnings_dt and earnings_dt - state.date <= timedelta(days=self.limits.wheel_earnings_blackout_days):
                return ExecutionDecision(approved=False, reason="Wheel earnings blackout active")

        return ExecutionDecision(approved=True, reason="Within risk limits")
