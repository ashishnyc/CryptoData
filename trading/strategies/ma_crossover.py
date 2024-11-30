import pandas as pd
import numpy as np
from typing import Union


class MACrossoverStrategy:
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window
        self.short_ma = []
        self.long_ma = []
        self.prices = []

    def generate_signal(self, bar: pd.Series) -> Union[str, None]:
        """
        Generate trading signal based on MA crossover
        Returns: 'BUY', 'SELL', or None
        """
        # Add current price to list
        self.prices.append(bar.close)

        # Wait for enough prices
        if len(self.prices) < self.long_window:
            return None

        # Calculate MAs
        self.short_ma = pd.Series(self.prices).rolling(self.short_window).mean()
        self.long_ma = pd.Series(self.prices).rolling(self.long_window).mean()

        # Generate signals
        if len(self.prices) > self.long_window:
            # Crossover up (short MA crosses above long MA)
            if (
                self.short_ma.iloc[-2] <= self.long_ma.iloc[-2]
                and self.short_ma.iloc[-1] > self.long_ma.iloc[-1]
            ):
                return "BUY"

            # Crossover down (short MA crosses below long MA)
            elif (
                self.short_ma.iloc[-2] >= self.long_ma.iloc[-2]
                and self.short_ma.iloc[-1] < self.long_ma.iloc[-1]
            ):
                return "SELL"

        return None
