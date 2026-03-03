from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RiskLimits(BaseModel):
    risk_per_trade_pct: float = Field(default=0.01, le=0.01)
    max_daily_loss_pct: float = Field(default=0.025, le=0.025)
    max_concurrent_earnings: int = Field(default=3)
    wheel_earnings_blackout_days: int = Field(default=10)
    assignment_exposure_cap_pct: float = Field(default=0.25, le=0.25)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    app_env: Literal["dev", "prod"] = "prod"
    bot_host: str = "127.0.0.1"
    bot_port: int = 8000
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8080

    alpaca_api_key: SecretStr
    alpaca_secret_key: SecretStr
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    # Render paper mode default (persist with Render Disk mounted at /var/data)
    database_url: str = "sqlite:////var/data/trading.db"
    discord_webhook_url: SecretStr | None = None
    dashboard_admin_token: SecretStr

    request_timeout_seconds: float = 15
    max_retries: int = 4
    cycle_interval_seconds: int = 300

    risk_limits: RiskLimits = RiskLimits()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
