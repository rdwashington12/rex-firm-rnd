from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class EngineName(str, Enum):
    TACTICAL_EARNINGS = "tactical_earnings"
    DRIFT = "drift"
    WHEEL = "wheel"


class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"


class TradeIdea(BaseModel):
    engine: EngineName
    symbol: str
    strategy: str
    notional_risk: float = Field(gt=0)
    horizon_days: int
    tags: list[str] = Field(default_factory=list)


class ExecutionDecision(BaseModel):
    approved: bool
    reason: str


class TradingState(BaseModel):
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    day_pnl_pct: float = 0.0
    open_earnings_trades: int = 0
    assignment_exposure_pct: float = 0.0
    earnings_calendar: dict[str, datetime] = Field(default_factory=dict)


class ControlState(BaseModel):
    tactical_earnings_enabled: bool = True
    drift_enabled: bool = True
    wheel_enabled: bool = True
    risk_mode: Literal["normal", "reduce", "flat"] = "normal"
    kill_switch: bool = False
    whitelist: list[str] = Field(default_factory=list)
    blacklist: list[str] = Field(default_factory=list)
