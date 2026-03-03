from abc import ABC, abstractmethod

from app.domain.models import TradeIdea, TradingState


class Engine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate(self, state: TradingState) -> list[TradeIdea]:
        raise NotImplementedError
