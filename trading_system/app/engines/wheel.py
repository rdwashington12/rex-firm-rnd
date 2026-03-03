from app.domain.models import EngineName, TradeIdea, TradingState
from app.engines.base import Engine


class WheelEngine(Engine):
    @property
    def name(self) -> str:
        return EngineName.WHEEL.value

    def generate(self, state: TradingState) -> list[TradeIdea]:
        return [
            TradeIdea(
                engine=EngineName.WHEEL,
                symbol="KO",
                strategy="cash_secured_put",
                notional_risk=0.005,
                horizon_days=14,
                tags=["income", "wheel"],
            )
        ]
