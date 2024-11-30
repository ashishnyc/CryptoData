# trading/optimization/optimizer.py

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from itertools import product
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor
from ..engine.backtest import BacktestEngine
from ..strategies.ma_crossover import MACrossoverStrategy


class StrategyOptimizer:
    def __init__(self, data: pd.DataFrame, initial_capital: float = 10000):
        self.data = data
        self.initial_capital = initial_capital
        self.results = []

    def optimize_ma_strategy(
        self, short_windows: List[int], long_windows: List[int], parallel: bool = False
    ) -> pd.DataFrame:
        """
        Test multiple combinations of moving averages
        """
        # Generate all combinations
        combinations = [
            (short, long)
            for short, long in product(short_windows, long_windows)
            if short < long
        ]

        if parallel:
            try:
                with ProcessPoolExecutor() as executor:
                    results = list(executor.map(self._test_parameters, combinations))
            except Exception as e:
                print(
                    f"Parallel processing failed, falling back to sequential: {str(e)}"
                )
                results = [self._test_parameters(params) for params in combinations]
        else:
            results = [self._test_parameters(params) for params in combinations]

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        results_df.sort_values("total_return", ascending=False, inplace=True)
        self.results = results_df
        return results_df

    def _test_parameters(self, params: Tuple[int, int]) -> Dict:
        """Run backtest with specific parameters"""
        short_window, long_window = params

        engine = BacktestEngine(initial_capital=self.initial_capital)
        strategy = MACrossoverStrategy(
            short_window=short_window, long_window=long_window
        )

        results = engine.run(self.data, strategy)

        return {
            "short_window": short_window,
            "long_window": long_window,
            "total_return": results["total_return"],
            "sharpe_ratio": results["sharpe_ratio"],
            "max_drawdown": results["max_drawdown"],
            "win_rate": results["win_rate"],
            "total_trades": results["total_trades"],
        }

    def plot_results(self):
        """Create visualization of optimization results"""
        if len(self.results) == 0:
            raise ValueError("No results to plot. Run optimize_ma_strategy first.")

        fig = plt.figure(figsize=(20, 10))

        # 1. Heatmap of returns
        plt.subplot(221)
        pivot_returns = self.results.pivot_table(
            index="short_window", columns="long_window", values="total_return"
        )
        sns.heatmap(pivot_returns, annot=True, fmt=".1f", cmap="RdYlGn")
        plt.title("Total Returns (%)")

        # 2. Heatmap of Sharpe ratios
        plt.subplot(222)
        pivot_sharpe = self.results.pivot_table(
            index="short_window", columns="long_window", values="sharpe_ratio"
        )
        sns.heatmap(pivot_sharpe, annot=True, fmt=".2f", cmap="RdYlGn")
        plt.title("Sharpe Ratio")

        # 3. Scatter plot of returns vs trades
        plt.subplot(223)
        plt.scatter(
            self.results["total_trades"], self.results["total_return"], alpha=0.5
        )
        plt.xlabel("Number of Trades")
        plt.ylabel("Total Return (%)")
        plt.title("Returns vs Number of Trades")

        # 4. Top 10 combinations
        plt.subplot(224)
        top_10 = self.results.head(10)
        x = range(len(top_10))
        plt.bar(x, top_10["total_return"])
        plt.xticks(
            x,
            [f"{s}/{l}" for s, l in zip(top_10["short_window"], top_10["long_window"])],
            rotation=45,
        )
        plt.xlabel("MA Combinations (Short/Long)")
        plt.ylabel("Total Return (%)")
        plt.title("Top 10 Combinations")

        plt.tight_layout()
        return fig

    def get_top_parameters(self, n: int = 10) -> pd.DataFrame:
        """Get top n parameter combinations"""
        return self.results.head(n)

    def plot_detailed_comparison(self, n_best: int = 3):
        """Plot equity curves for top n strategies"""
        top_n = self.results.head(n_best)

        # Run detailed backtest for each top combination
        equity_curves = []

        for _, row in top_n.iterrows():
            engine = BacktestEngine(initial_capital=self.initial_capital)
            strategy = MACrossoverStrategy(
                short_window=int(row["short_window"]),
                long_window=int(row["long_window"]),
            )
            results = engine.run(self.data, strategy)
            equity_curves.append(
                {
                    "short": row["short_window"],
                    "long": row["long_window"],
                    "equity": results["equity_curve"]["equity"],
                }
            )

        # Plot comparison
        plt.figure(figsize=(15, 7))

        # Plot price normalized
        price_norm = (
            self.data["close"] / self.data["close"].iloc[0] * self.initial_capital
        )
        plt.plot(price_norm, label="Buy & Hold", color="gray", alpha=0.5)

        # Plot equity curves
        for curve in equity_curves:
            label = f"MA {curve['short']}/{curve['long']}"
            plt.plot(curve["equity"], label=label)

        plt.title("Strategy Comparison - Equity Curves")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value ($)")
        plt.legend()
        plt.grid(True)

        return plt.gcf()
