from typing import Dict, Optional
import pandas as pd
from datetime import datetime
from trading.Engine.Event import EventPublisher, Event, EventType, EngineClock
from trading.Engine.Broker import Broker
from Config import settings


class BacktestEngine:
    def __init__(self):
        self.strategy = None
        self.current_positions = {}

    def set_strategy(self, strategy):
        self.strategy = strategy

    async def run(self):
        if not self.strategy:
            raise ValueError("No strategy set")
        # Initialize the strategy
        self.strategy.init()

        # Create and configure the engine clock
        clock = EngineClock(
            start_time=self.strategy.start_date,
            end_time=self.strategy.end_date,
        )

        # Add timeframes from strategy
        clock.add_timeframe(self.strategy.timeframe)

        # Subscribe to events
        clock.events.subscribe(EventType.BAR_CLOSED, self.strategy.on_event)

        # Store clock reference in strategy
        self.strategy.engine_clock = clock

        # Run the clock
        print(
            f"Starting backtest from {self.strategy.start_date} to {self.strategy.end_date}"
        )
        await clock.run()
        print("Backtest completed")
