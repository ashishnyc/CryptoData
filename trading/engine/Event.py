import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple


class EventType(Enum):
    BAR_CLOSED = "BAR_CLOSED"
    ORDER_FILLED = "ORDER_FILLED"
    TRADE_CLOSED = "TRADE_CLOSED"


class Event:
    def __init__(self, event_type: EventType, data: dict):
        self.type = event_type
        self.data = data
        self.timestamp = datetime.now()


class EventPublisher:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: Event):
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                callback(event)


class Timeframe:
    TIMEFRAMES = {
        "1min": timedelta(minutes=1),
        "5min": timedelta(minutes=5),
        "15min": timedelta(minutes=15),
        "30min": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }

    @staticmethod
    def _parse_timeframe(timeframe: str) -> Tuple[int, str]:
        """Parse timeframe string into value and unit."""
        if timeframe not in Timeframe.TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe format: {timeframe}")

        if timeframe.endswith("min"):
            return int(timeframe[:-3]), "min"
        elif timeframe.endswith("h"):
            return int(timeframe[:-1]), "h"
        elif timeframe == "1d":
            return 1, "d"
        raise ValueError(f"Unsupported timeframe format: {timeframe}")

    @staticmethod
    def get_previous_boundary(dt: datetime, timeframe: str) -> datetime:
        value, unit = Timeframe._parse_timeframe(timeframe)

        if unit == "min":
            return dt.replace(
                minute=dt.minute - (dt.minute % value), second=0, microsecond=0
            )
        elif unit == "h":
            return dt.replace(
                hour=dt.hour - (dt.hour % value), minute=0, second=0, microsecond=0
            )
        elif unit == "d":
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

        raise ValueError(f"Unsupported timeframe unit: {unit}")

    @staticmethod
    def is_boundary(dt: datetime, timeframe: str) -> bool:
        value, unit = Timeframe._parse_timeframe(timeframe)

        if unit == "min":
            return dt.minute % value == 0 and dt.second == 0
        elif unit == "h":
            return dt.hour % value == 0 and dt.minute == 0 and dt.second == 0
        elif unit == "d":
            return dt.hour == 0 and dt.minute == 0 and dt.second == 0

        raise ValueError(f"Unsupported timeframe unit: {unit}")


class EngineClock:
    def __init__(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ):
        self.events = EventPublisher()
        self.start_time = start_time
        self.current_time = start_time
        self.end_time = end_time
        self.is_running = False
        self.timeframes = set()
        self.base_delta = timedelta(minutes=1)
        self.backtesting_mode = end_time is not None
        self._last_boundaries = {}

    def add_timeframe(self, timeframe: str):
        if timeframe not in Timeframe.TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        self.timeframes.add(timeframe)
        self._last_boundaries[timeframe] = Timeframe.get_previous_boundary(
            self.start_time, timeframe
        )

    def _check_timeframe_closures(self, current_time: datetime):
        for timeframe in self.timeframes:
            current_boundary = Timeframe.get_previous_boundary(current_time, timeframe)
            last_boundary = self._last_boundaries[timeframe]

            if current_boundary > last_boundary:
                self.events.publish(
                    Event(
                        EventType.BAR_CLOSED,
                        {
                            "timeframe": timeframe,
                            "opened_at": last_boundary,
                            "closed_at": current_boundary - timedelta(seconds=1),
                        },
                    )
                )
                self._last_boundaries[timeframe] = current_boundary

    async def run(self):
        if not self.timeframes:
            raise ValueError("No timeframes added")

        self.is_running = True

        while self.is_running:
            if self.end_time and self.current_time >= self.end_time:
                self.stop()
                break

            if self.backtesting_mode:
                self.current_time += self.base_delta
            else:
                await asyncio.sleep(self.base_delta.seconds)
                self.current_time = datetime.now()

            self._check_timeframe_closures(self.current_time)

    def stop(self):
        self.is_running = False


async def main():
    # Example of backtesting mode
    backtest_clock = EngineClock(
        start_time=datetime(2023, 1, 1),
        end_time=datetime(2024, 12, 21),
    )
    backtest_clock.add_timeframe("1h")

    def on_bar_closed(event: Event):
        print(f"Bar closed for {event.data['timeframe']} at {event.data['timestamp']}")
        print(f"  Opened at: {event.data['opened_at']}")
        print(f"  Closed at: {event.data['closed_at']}")

    backtest_clock.events.subscribe(EventType.BAR_CLOSED, on_bar_closed)

    print("Starting backtesting mode...")
    import time

    t1 = time.time()
    await backtest_clock.run()
    t2 = time.time()
    print(f"Backtesting completed in {t2 - t1:.2f} seconds")

    # Example of real-time mode
    realtime_clock = EngineClock(
        start_time=datetime.now(),
        end_time=None,
    )
    realtime_clock.add_timeframe("5min")
    realtime_clock.events.subscribe(EventType.BAR_CLOSED, on_bar_closed)

    print("\nStarting real-time mode...")
    await realtime_clock.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClock stopped by user")
