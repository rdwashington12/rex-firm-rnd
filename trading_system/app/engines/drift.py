from app.domain.models import EngineName, TradeIdea, TradingState
from app.engines.base import Engine


class DriftEngine(Engine):
    @property
    def name(self) -> str:
        return EngineName.DRIFT.value

    def generate(self, state: TradingState) -> list[TradeIdea]:
        return [
            TradeIdea(
                engine=EngineName.DRIFT,
                symbol="MSFT",
                strategy="directional_call_debit",
                notional_risk=0.006,
                horizon_days=10,
                tags=["swing", "drift"],
            )
        ]
