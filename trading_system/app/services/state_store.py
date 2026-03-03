from threading import Lock

from app.domain.models import ControlState, TradingState


class InMemoryStateStore:
    def __init__(self) -> None:
        self._control = ControlState()
        self._trading = TradingState()
        self._lock = Lock()

    def get_control(self) -> ControlState:
        with self._lock:
            return self._control.model_copy(deep=True)

    def update_control(self, control: ControlState) -> ControlState:
        with self._lock:
            self._control = control
            return self._control.model_copy(deep=True)

    def get_trading(self) -> TradingState:
        with self._lock:
            return self._trading.model_copy(deep=True)

    def update_trading(self, trading: TradingState) -> TradingState:
        with self._lock:
            self._trading = trading
            return self._trading.model_copy(deep=True)
