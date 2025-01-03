import asyncio
import pandas as pd
import numpy as np
from typing import Union
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from trading.Strategies.BaseStrategy import BaseStrategy
from trading.Engine.Backtest import BacktestEngine


class MACrossoverStrategy(BaseStrategy):
    def init(self):
        # Initialize strategy parameters
        self.symbols = ["AAPL"]
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.timeframe = "1h"

        # Moving average parameters
        self.short_window = 20  # 20-day moving average
        self.long_window = 50  # 50-day moving average

        # Store historical data
        self._bars = []
        self.positions = {}  # Track open positions

        # Initialize indicators
        self.short_ma = None
        self.long_ma = None

    def calculate_moving_averages(self):
        """Calculate short and long moving averages from stored bars"""
        if len(self._bars) > self.long_window:
            df = pd.DataFrame(self._bars)

            # Calculate moving averages
            self.short_ma = (
                df["close"].rolling(window=self.short_window).mean().iloc[-1]
            )
            self.long_ma = df["close"].rolling(window=self.long_window).mean().iloc[-1]

            return True
        return False

    def generate_signals(self, current_price: float) -> str:
        """Generate trading signals based on MA crossover"""
        if self.short_ma is None or self.long_ma is None:
            return "HOLD"

        # Golden Cross (Short MA crosses above Long MA)
        if self.short_ma > self.long_ma:
            return "BUY"
        # Death Cross (Short MA crosses below Long MA)
        elif self.short_ma < self.long_ma:
            return "SELL"
        else:
            return "HOLD"

    def on_event(self, event: dict):
        """Handle incoming market data events"""
        # Store the new bar
        self._bars.append(event.data)
        print(event.data)
        # current_price = event.data["close"]

        # # Calculate indicators
        # if self.calculate_moving_averages():
        #     # Generate trading signal
        #     signal = self.generate_signals(current_price)

        #     # Execute trades based on signals
        #     symbol = event.data["symbol"]

        #     if signal == "BUY" and symbol not in self.positions:
        #         # Calculate position size (example: invest 100% of capital)
        #         size = self.get_portfolio_value() / current_price
        #         self.create_order(symbol, "BUY", size)
        #         self.positions[symbol] = size

        #     elif signal == "SELL" and symbol in self.positions:
        #         # Close position
        #         self.create_order(symbol, "SELL", self.positions[symbol])
        #         del self.positions[symbol]

        # # Print current state
        # print(
        #     f"Price: {current_price:.2f}, Short MA: {self.short_ma:.2f}, Long MA: {self.long_ma:.2f}"
        # )


# Usage example
async def main():
    strategy = MACrossoverStrategy()
    backtester = BacktestEngine()
    backtester.set_strategy(strategy)
    await backtester.run()

    # Analysis of results
    df = pd.DataFrame(strategy._bars)
    print("\nBacktest Results:")
    print(f"Total Trades: {len(df)}")


if __name__ == "__main__":
    asyncio.run(main())
