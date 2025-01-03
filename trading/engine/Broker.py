from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from trading.Engine.Event import EventPublisher, Event, EventType
import pandas as pd


@dataclass
class Order:
    symbol: str
    side: str
    entry_price: Decimal
    quantity: Decimal
    timestamp: datetime
    fee_rate: Decimal = Decimal("0.001")
    status: str = "PENDING"
    execution_price: Optional[Decimal] = None
    execution_time: Optional[datetime] = None


@dataclass
class Trade:
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime = None
    exit_price: float = None
    quantity: float = 0
    side: str = "BUY"
    pnl: float = 0
    status: str = "OPEN"


class Broker:
    def __init__(
        self,
        initial_capital: Decimal = Decimal("10000"),
        default_fee_rate: Decimal = Decimal("0.001"),
    ):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.default_fee_rate = default_fee_rate
        self.trades: List[Trade] = []
        self.current_trade: Optional[Trade] = None
        self.events = EventPublisher()
        self.pending_orders: List[Order] = []

        self.events.subscribe(EventType.BAR_CLOSED, self._process_orders)

        self.equity_curve = pd.DataFrame(
            columns=["timestamp", "equity", "drawdown", "drawdown_pct", "price"]
        )

    def place_order(
        self,
        timestamp: datetime,
        price: Decimal,
        side: str,
        symbol: str,
        quantity: Optional[Decimal] = None,
        fee_rate: Optional[Decimal] = None,
    ) -> bool:
        if quantity is None:
            quantity = (self.capital * Decimal("0.95")) / price

        if fee_rate is None:
            fee_rate = self.default_fee_rate

        cost = quantity * price * (Decimal("1") + fee_rate)
        if cost > self.capital:
            return False

        order = Order(
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=quantity,
            timestamp=timestamp,
            fee_rate=fee_rate,
        )

        self.pending_orders.append(order)
        return True

    def _process_orders(self, event: Event):
        if event.data.get("timeframe") != "5min":
            return

        bar_data = event.data
        high_price = Decimal(str(bar_data.get("high")))
        low_price = Decimal(str(bar_data.get("low")))

        for order in self.pending_orders[:]:
            if order.side == "BUY" and low_price <= order.entry_price <= high_price:
                self._execute_order(order, order.entry_price, event.data["closed_at"])
            elif order.side == "SELL" and low_price <= order.entry_price <= high_price:
                self._execute_order(order, order.entry_price, event.data["closed_at"])

    def _execute_order(
        self, order: Order, execution_price: Decimal, execution_time: datetime
    ):
        order.status = "EXECUTED"
        order.execution_price = execution_price
        order.execution_time = execution_time

        self.pending_orders.remove(order)

        cost = order.quantity * execution_price * (Decimal("1") + order.fee_rate)
        if cost <= self.capital:
            self.current_trade = Trade(
                symbol=order.symbol,
                entry_time=execution_time,
                entry_price=execution_price,
                quantity=order.quantity,
                side=order.side,
            )
            self.capital -= cost
            self.trades.append(self.current_trade)

            self.events.publish(
                Event(
                    EventType.ORDER_FILLED,
                    {
                        "timestamp": execution_time,
                        "price": execution_price,
                        "side": order.side,
                        "quantity": order.quantity,
                        "fee_rate": order.fee_rate,
                    },
                )
            )
