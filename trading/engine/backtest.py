# trading/engine/backtest.py

from dataclasses import dataclass
from typing import List, Dict
import pandas as pd
import numpy as np
from datetime import datetime


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


class BacktestEngine:
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission = commission
        self.trades: List[Trade] = []
        self.current_trade: Trade = None

        # Enhanced tracking of results
        self.equity_curve = pd.DataFrame(
            columns=["timestamp", "equity", "drawdown", "drawdown_pct", "price"]
        )
        self.positions: Dict = {}

    def run(self, data: pd.DataFrame, strategy, symbol: str = "UNKNOWN") -> Dict:
        """
        Run backtest on historical data using given strategy
        """
        # Ensure data is sorted by time
        data = data.sort_index()

        # Initialize equity curve with initial capital
        self.equity_curve = pd.DataFrame(index=data.index)
        self.equity_curve["equity"] = self.initial_capital
        self.equity_curve["price"] = data["close"]  # Track price

        # Run strategy on each bar
        for timestamp, bar in data.iterrows():
            # Update strategy
            signal = strategy.generate_signal(bar)

            # Execute trades based on signals
            if signal and self.current_trade is None:  # No open position
                if signal == "BUY":
                    self._open_trade(timestamp, bar["close"], "BUY", symbol)
            elif signal and self.current_trade:  # Have open position
                if signal == "SELL":
                    self._close_trade(timestamp, bar["close"])

            # Update equity curve
            self._update_equity(timestamp, bar["close"])

        # Close any remaining positions at the last price
        if self.current_trade:
            last_timestamp = data.index[-1]
            last_price = data.iloc[-1]["close"]
            self._close_trade(last_timestamp, last_price)

        # Calculate drawdown series
        self._calculate_drawdown()

        # Calculate price performance
        self.equity_curve["price_performance"] = (
            self.equity_curve["price"] / self.equity_curve["price"].iloc[0] - 1
        ) * 100

        return self._generate_results()

    def _open_trade(self, timestamp: datetime, price: float, side: str, symbol: str):
        """Open new trade"""
        quantity = (self.capital * 0.95) / price  # Use 95% of capital
        cost = quantity * price * (1 + self.commission)

        if cost <= self.capital:
            self.current_trade = Trade(
                symbol=symbol,
                entry_time=timestamp,
                entry_price=price,
                quantity=quantity,
                side=side,
            )
            self.capital -= cost
            self.trades.append(self.current_trade)

    def _close_trade(self, timestamp: datetime, price: float):
        """Close current trade"""
        if self.current_trade:
            self.current_trade.exit_time = timestamp
            self.current_trade.exit_price = price

            # Calculate PnL
            exit_value = self.current_trade.quantity * price * (1 - self.commission)
            entry_value = self.current_trade.quantity * self.current_trade.entry_price

            self.current_trade.pnl = exit_value - entry_value
            self.current_trade.status = "CLOSED"

            # Update capital
            self.capital += exit_value
            self.current_trade = None

    def _update_equity(self, timestamp: datetime, current_price: float):
        """Update equity curve with current timestamp"""
        equity = self.capital
        if self.current_trade:
            equity += self.current_trade.quantity * current_price
        self.equity_curve.at[timestamp, "equity"] = equity

    def _calculate_drawdown(self):
        """Calculate drawdown and drawdown percentage series"""
        equity = self.equity_curve["equity"]
        rolling_max = equity.expanding().max()
        self.equity_curve["drawdown"] = equity - rolling_max
        self.equity_curve["drawdown_pct"] = (
            self.equity_curve["drawdown"] / rolling_max
        ) * 100

    def _generate_results(self) -> Dict:
        """Generate backtest results and statistics"""
        equity = self.equity_curve["equity"]
        returns = equity.pct_change().dropna()

        # Calculate metrics
        total_return = (equity.iloc[-1] / self.initial_capital - 1) * 100
        sharpe_ratio = (
            np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0
        )

        # Calculate trade statistics
        profitable_trades = len([t for t in self.trades if t.pnl > 0])
        total_trades = len(self.trades)

        # Get worst drawdown time period
        worst_dd_idx = self.equity_curve["drawdown_pct"].idxmin()

        return {
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(float(self.equity_curve["drawdown_pct"].min()), 2),
            "max_drawdown_date": worst_dd_idx,
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "win_rate": round(
                profitable_trades / total_trades * 100 if total_trades > 0 else 0, 2
            ),
            "final_capital": round(float(equity.iloc[-1]), 2),
            "equity_curve": self.equity_curve,
            "trades": self._generate_trade_history(),
        }

    def _generate_trade_history(self) -> pd.DataFrame:
        """Generate detailed trade history DataFrame"""
        trades_data = []
        for trade in self.trades:
            trades_data.append(
                {
                    "entry_time": trade.entry_time,
                    "exit_time": trade.exit_time,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "quantity": trade.quantity,
                    "pnl": trade.pnl,
                    "return_pct": (trade.pnl / (trade.entry_price * trade.quantity))
                    * 100,
                }
            )
        return pd.DataFrame(trades_data)
