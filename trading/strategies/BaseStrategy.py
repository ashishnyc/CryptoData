from abc import ABCMeta, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional


class BaseStrategy(metaclass=ABCMeta):
    def __init__(self):
        self.symbols: List[str] = []
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.initial_capital: Decimal = Decimal("10000")
        self.timeframe: str = "1d"
        self._position: Dict[str, Decimal] = {}
        self.engine_clock = None

    def set_start_date(self, year: int, month: int, day: int) -> None:
        """Set the backtest start date"""
        self.start_date = datetime(year, month, day)

    def set_end_date(self, year: int, month: int, day: int) -> None:
        """Set the backtest end date"""
        self.end_date = datetime(year, month, day)

    def set_holdings(self, symbol: str, target_percentage: Decimal) -> None:
        """Set target holdings for a symbol as a percentage of portfolio"""
        self._position[symbol] = target_percentage

    @abstractmethod
    def init(self) -> None:
        """Initialize the strategy, define symbols, timeframe, and other parameters"""
        raise NotImplementedError("initialize method not implemented")

    @abstractmethod
    def on_event(self, event: dict) -> None:
        """Handle new bar data"""
        raise NotImplementedError("on_bar method not implemented")

    def get_positions(self) -> Dict[str, float]:
        """Get current positions"""
        return self._position.copy()
