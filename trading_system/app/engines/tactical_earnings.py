from app.domain.models import EngineName, TradeIdea, TradingState
from app.engines.base import Engine


class TacticalEarningsEngine(Engine):
    @property
    def name(self) -> str:
        return EngineName.TACTICAL_EARNINGS.value

    def generate(self, state: TradingState) -> list[TradeIdea]:
        return [
            TradeIdea(
                engine=EngineName.TACTICAL_EARNINGS,
                symbol="AAPL",
                strategy="earnings_debit_spread",
                notional_risk=0.0075,
                horizon_days=2,
                tags=["intraday", "earnings"],
            )
        ]
