from typing import Literal

from pydantic import BaseModel, Field


class ControlUpdate(BaseModel):
    tactical_earnings_enabled: bool
    drift_enabled: bool
    wheel_enabled: bool
    risk_mode: Literal["normal", "reduce", "flat"]
    kill_switch: bool
    whitelist: list[str] = Field(default_factory=list)
    blacklist: list[str] = Field(default_factory=list)
