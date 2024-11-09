from pybit.unified_trading import HTTP
from typing import Dict, List, Optional, Union
from enum import Enum
from datetime import datetime, timedelta, date


class Category(Enum):
    LINEAR = "linear"
    INVERSE = "inverse"
    SPOT = "spot"
    OPTION = "option"


class ContractType(Enum):
    INVERSE_PERPETUAL = "InversePerpetual"
    LINEAR_PERPETUAL = "LinearPerpetual"
    LINEAR_FUTURES = "LinearFutures"
    INVERST_FUTURES = "InverseFutures"


class Interval(Enum):
    _1_MIN = "1"
    _3_MIN = "3"
    _5_MIN = "5"
    _15_MIN = "15"
    _30_MIN = "30"
    _1_HOUR = "60"
    _2_HOUR = "120"
    _4_HOUR = "240"
    _6_HOUR = "360"
    _12_HOUR = "720"
    _1_DAY = "D"
    _1_WEEK = "W"
    _1_MONTH = "M"


class MarketData:
    def __init__(
        self, testnet: bool = False, api_key: str = None, api_secret: str = None
    ):
        self.session = HTTP(testnet=testnet, api_key=api_key, api_secret=api_secret)

    def fetch_instruments(
        self,
        category: Category,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Fetch instruments for a specific category"""
        params = {"category": category.value}
        if limit:
            params["limit"] = limit

        try:
            response = self.session.get_instruments_info(**params)
            return response.get("result", {}).get("list", [])
        except Exception as e:
            print(f"Error fetching instruments for {category.value}: {str(e)}")
            return []

    def fetch_all_instruments(
        self, limit: Optional[int] = None
    ) -> Dict[str, List[Dict]]:
        """Fetch instruments for all categories"""
        results = {}
        for category in Category:
            results[category.value] = self.fetch_instruments(category, limit)
        return results

    def fetch_kline(
        self,
        category: Category,
        symbol: str,
        interval: Interval,
        start_time: Optional[Union[int, datetime]] = None,
        end_time: Optional[Union[int, datetime]] = None,
        limit: int = 1000,
    ) -> List[Dict]:
        """
        Fetch Kline/candlestick data for a specific symbol

        Args:
            category: Market category (linear, inverse, spot)
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval
            start_time: Start time in timestamp (milliseconds) or datetime
            end_time: End time in timestamp (milliseconds) or datetime
            limit: Maximum number of records to return (default: 1000)
        """
        params = {
            "category": category.value,
            "symbol": symbol,
            "interval": interval.value,
            "limit": limit,
        }

        # Convert datetime to timestamp if provided
        if isinstance(start_time, datetime):
            params["start"] = int(start_time.timestamp() * 1000)
        elif start_time is not None:
            params["start"] = start_time

        if isinstance(end_time, datetime):
            params["end"] = int(end_time.timestamp() * 1000)
        elif end_time is not None:
            params["end"] = end_time

        try:
            response = self.session.get_kline(**params)
            return response.get("result", {}).get("list", [])
        except Exception as e:
            print(f"Error fetching kline data for {symbol}: {str(e)}")
            return []

    def fetch_kline_for_date(
        self,
        category: Category,
        symbol: str,
        interval: Interval,
        kline_date: date,
        limit: int = 1000,
    ) -> List[Dict]:
        start_time = datetime.combine(kline_date, datetime.min.time())
        end_time = start_time + timedelta(days=1) - timedelta(seconds=1)
        return self.fetch_kline(category, symbol, interval, start_time, end_time, limit)
