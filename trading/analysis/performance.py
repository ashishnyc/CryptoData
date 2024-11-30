import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.gridspec import GridSpec


class PerformanceAnalyzer:
    def __init__(self, results: dict):
        self.results = results
        self.equity_curve = results["equity_curve"]
        self.trades = results["trades"]

    def plot_full_analysis(self):
        """Create a comprehensive performance analysis plot"""
        fig = plt.figure(figsize=(15, 12))
        gs = GridSpec(4, 1, figure=fig)

        # Plot 1: Price and Strategy Performance
        ax1 = fig.add_subplot(gs[0:2])

        # Plot price on left y-axis
        ax1.plot(
            self.equity_curve.index,
            self.equity_curve["price"],
            color="gray",
            alpha=0.6,
            label="Price",
        )
        ax1.set_ylabel("Price ($)", color="gray")
        ax1.tick_params(axis="y", labelcolor="gray")

        # Plot equity on right y-axis
        ax2 = ax1.twinx()
        ax2.plot(
            self.equity_curve.index,
            self.equity_curve["equity"],
            color="blue",
            label="Portfolio Value",
        )
        ax2.set_ylabel("Portfolio Value ($)", color="blue")
        ax2.tick_params(axis="y", labelcolor="blue")

        # Add trade markers
        for trade in self.trades.itertuples():
            ax1.axvline(x=trade.entry_time, color="g", alpha=0.2)
            if trade.exit_time:
                ax1.axvline(x=trade.exit_time, color="r", alpha=0.2)

        ax1.set_title("Price and Portfolio Performance")
        ax1.grid(True, alpha=0.3)

        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

        # Plot 2: Drawdown
        ax3 = fig.add_subplot(gs[2])
        self.equity_curve["drawdown_pct"].plot(ax=ax3, color="red", label="Drawdown %")
        ax3.fill_between(
            self.equity_curve.index,
            self.equity_curve["drawdown_pct"],
            0,
            color="red",
            alpha=0.3,
        )
        ax3.set_title("Drawdown Percentage")
        ax3.set_ylabel("Drawdown %")
        ax3.grid(True)
        ax3.legend()

        # Plot 3: Relative Performance
        ax4 = fig.add_subplot(gs[3])
        price_perf = self.equity_curve["price_performance"]
        equity_perf = (
            self.equity_curve["equity"] / self.equity_curve["equity"].iloc[0] - 1
        ) * 100

        ax4.plot(
            self.equity_curve.index,
            price_perf,
            label="Buy & Hold",
            color="gray",
            alpha=0.6,
        )
        ax4.plot(self.equity_curve.index, equity_perf, label="Strategy", color="blue")
        ax4.set_title("Strategy vs Buy & Hold Performance (%)")
        ax4.set_ylabel("Return %")
        ax4.grid(True)
        ax4.legend()

        plt.tight_layout()
        return fig

    def generate_report(self):
        """Generate a text report of key statistics"""
        initial_price = self.equity_curve["price"].iloc[0]
        final_price = self.equity_curve["price"].iloc[-1]
        buy_hold_return = (final_price / initial_price - 1) * 100

        report = [
            "Performance Report",
            "=" * 50,
            f"Total Return: {self.results['total_return']}%",
            f"Buy & Hold Return: {buy_hold_return:.2f}%",
            f"Outperformance: {self.results['total_return'] - buy_hold_return:.2f}%",
            f"Sharpe Ratio: {self.results['sharpe_ratio']}",
            f"Maximum Drawdown: {self.results['max_drawdown']}%",
            f"Max Drawdown Date: {self.results['max_drawdown_date']}",
            f"Total Trades: {self.results['total_trades']}",
            f"Win Rate: {self.results['win_rate']}%",
            # f"Initial Capital: ${self.results['initial_capital']:.2f}",
            f"Final Capital: ${self.results['final_capital']:.2f}",
            f"Initial Price: ${initial_price:.2f}",
            f"Final Price: ${final_price:.2f}",
            "=" * 50,
        ]
        return "\n".join(report)

    def save_results(self, filename: str):
        """Save results to CSV files"""
        self.equity_curve.to_csv(f"{filename}_equity.csv")
        if len(self.trades) > 0:
            self.trades.to_csv(f"{filename}_trades.csv")
