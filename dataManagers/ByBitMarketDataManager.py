import asyncio
from collections import defaultdict
from decimal import Decimal
import json
from sqlmodel import Session, and_, select, text, insert, SQLModel, func
from xchanges.ByBit import MarketData, Category, Interval, ContractType
from database.models import Market, PriceLevels
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database import Operations as dbOperations
from datetime import datetime, date, timedelta
import time
from typing import Any, Dict, Optional
import pandas as pd
from redis import ConnectionPool, Redis
from sqlmodel.ext.asyncio.session import AsyncSession
from collections import namedtuple
from utils import pivotid


class ByBitDataIngestion:
    def __init__(
        self, testnet: bool = False, api_key: str = None, api_secret: str = None
    ) -> None:
        self.dbClient = dbOperations.get_session()
        self.client = MarketData(
            testnet=testnet, api_key=api_key, api_secret=api_secret
        )

        self.default_interval = Interval._5_MIN
        self.quote_coin = "USDT"
        self.instrument_status = "Trading"
        self.bb_data_service = ByBitDataService(dbClient=self.dbClient)

        # currently looking at 10 candles can extend to something like [10, 20, 30]
        self.pivots_lookbacks = [10]
        self.pivots_timeframes = ["1h"]

    def download_linear_usdt_instruments(self, limit=1000):
        # Fetch ByBit instruments
        bb_instruments = self.client.fetch_instruments(
            category=Category.LINEAR,
            status=self.instrument_status,
            limit=limit,
        )
        bb_instruments_map = {
            instrument["symbol"]: instrument for instrument in bb_instruments
        }
        # Fetch Database Instruments
        db_instruments = self.bb_data_service.get_linear_usdt_instruments(
            quote_coin=self.quote_coin
        )
        db_instruments_map = {
            instrument.symbol: instrument for instrument in db_instruments
        }

        inserts, updates, deletes = 0, 0, 0
        for bb_symbol, bb_instrument in bb_instruments_map.items():
            current_instrument = self._convert_xchange_instruments_dict(bb_instrument)
            # Skip if not USDT
            if current_instrument.quote_coin != self.quote_coin:
                continue
            existing_instrument = db_instruments_map.get(bb_symbol)
            if existing_instrument:
                if not existing_instrument.is_equal(current_instrument):
                    updates += 1
                    self.dbClient.add(existing_instrument)
            else:
                self.dbClient.add(current_instrument)
                inserts += 1

        for db_symbol, db_instrument in db_instruments_map.items():
            if db_symbol not in bb_instruments_map:
                self.dbClient.delete(db_instrument)
                deletes += 1
        self.dbClient.commit()
        print(
            f"Processed linear USDT instruments: {inserts} inserts, {updates} updates, {deletes} deletes"
        )
        return (inserts, updates, deletes)

    def _convert_xchange_instruments_dict(
        self, xchange_dict
    ) -> Market.ByBitLinearInstruments:
        bb = Market.ByBitLinearInstruments()
        bb.set_symbol(xchange_dict["symbol"])
        bb.set_base_coin(xchange_dict["baseCoin"])
        bb.set_quote_coin(xchange_dict["quoteCoin"])
        bb.set_launch_time(xchange_dict["launchTime"])
        bb.set_price_scale(xchange_dict["priceScale"])
        bb.set_funding_interval(xchange_dict["fundingInterval"])
        bb.set_min_leverage(xchange_dict["leverageFilter"]["minLeverage"])
        bb.set_max_leverage(xchange_dict["leverageFilter"]["maxLeverage"])
        bb.set_leverage_step(xchange_dict["leverageFilter"]["leverageStep"])
        bb.set_max_trading_qty(xchange_dict["lotSizeFilter"]["maxOrderQty"])
        bb.set_min_trading_qty(xchange_dict["lotSizeFilter"]["minOrderQty"])
        bb.set_qty_step(xchange_dict["lotSizeFilter"]["qtyStep"])
        bb.set_min_price(xchange_dict["priceFilter"]["minPrice"])
        bb.set_max_price(xchange_dict["priceFilter"]["maxPrice"])
        bb.set_tick_size(xchange_dict["priceFilter"]["tickSize"])
        return bb

    def _download_linear_instruments_klines(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
    ):
        params = {
            "category": Category.LINEAR,
            "symbol": symbol,
            "interval": self.default_interval,
            "start_time": start_time,
            "end_time": end_time,
        }
        klines = self.client.fetch_kline(**params)
        if not klines:
            print(f"No klines found for {symbol}")
            return

        # Process Klines
        processed_klines = []
        for kline in klines:
            new_kline = Market.ByBitLinearInstrumentsKline5m()
            new_kline.set_symbol(symbol)
            new_kline.process_xchange_info(kline)
            processed_klines.append(new_kline)

        stmt = select(Market.ByBitLinearInstrumentsKline5m).where(
            and_(
                Market.ByBitLinearInstrumentsKline5m.symbol == symbol,
                Market.ByBitLinearInstrumentsKline5m.period_start
                <= datetime.fromtimestamp(int(klines[0][0]) / 1000),
                Market.ByBitLinearInstrumentsKline5m.period_start
                >= datetime.fromtimestamp(int(klines[-1][0]) / 1000),
            )
        )

        # Get existing records
        existing_records = {
            (record.symbol, record.period_start): record
            for record in self.dbClient.exec(stmt).all()
        }

        # Update existing records and create new ones
        to_update_or_create = []

        for kline in processed_klines:
            key = (kline.symbol, kline.period_start)
            existing = existing_records.get(key)
            if existing:
                # Skip if existing record is the same
                if existing.is_equal(kline):
                    continue

            stmt = self._update_insert_stmt_for_postgres(
                tbl=Market.ByBitLinearInstrumentsKline5m,
                data_for_insert=kline.to_dict(),
            )
            to_update_or_create.append(stmt)
            self.dbClient.exec(stmt)

        # Commit transaction
        try:
            self.dbClient.commit()
            print(
                f"Downloaded {symbol}({start_time} -> {end_time}) : updated/created {len(to_update_or_create)}"
            )

        except Exception as e:
            self.dbClient.rollback()
            print(f"Database error for {symbol}: {e}")
            raise

    def download_linear_instrument_klines(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        # Determine Parameters for Fetching Klines
        start_time = start_time or (datetime.now() - timedelta(minutes=15))
        end_time = end_time or datetime.now()

        # Determine Symbols to Download
        symbols_to_download = []
        if symbol is not None:
            symbols_to_download.append(symbol)
        else:
            all_instruments = self.bb_data_service.get_linear_usdt_instruments()
            symbols_to_download = [instrument.symbol for instrument in all_instruments]

        # Download Klines for each symbol
        for symbol in symbols_to_download:
            self._download_linear_instruments_klines(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
            )

    def download_klines_by_date(self, kline_date: date, symbol: str = None):
        start_time = datetime.combine(kline_date, datetime.min.time())
        end_time = start_time + timedelta(days=1) - timedelta(seconds=1)

        print(f"Downloading for {kline_date}({start_time} -> {end_time}), {symbol}")
        self.download_linear_instrument_klines(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
        )

    def _get_klines_aggregation_params(self, timeframe: str):
        params = namedtuple(
            "KlinesAggregationParams",
            ["target_table", "pandas_freq_str", "num_candles"],
        )
        if timeframe == "15m":
            return params(Market.ByBitLinearInstrumentsKline15m, "15min", 3)
        elif timeframe == "1h":
            return params(Market.ByBitLinearInstrumentsKline1h, "h", 12)
        elif timeframe == "4h":
            return params(Market.ByBitLinearInstrumentsKline4h, "4h", 48)
        elif timeframe == "1d":
            return params(Market.ByBitLinearInstrumentsKline1d, "D", 288)
        return None

    def _update_insert_stmt_for_postgres(self, tbl, data_for_insert=None):
        stmt = ""
        if data_for_insert:
            stmt = pg_insert(tbl)
            if "period_start" in data_for_insert:
                period_start_column = "period_start"
            elif "period_start_grouped" in data_for_insert:
                period_start_column = "period_start_grouped"

            data = {
                "symbol": data_for_insert["symbol"],
                "period_start": data_for_insert[period_start_column],
                "open_price": data_for_insert["open_price"],
                "high_price": data_for_insert["high_price"],
                "low_price": data_for_insert["low_price"],
                "close_price": data_for_insert["close_price"],
                "volume": data_for_insert["volume"],
                "turnover": data_for_insert["turnover"],
            }

        stmt = stmt.values(
            symbol=data["symbol"],
            period_start=data_for_insert[period_start_column],
            open_price=data["open_price"],
            high_price=data["high_price"],
            low_price=data["low_price"],
            close_price=data["close_price"],
            volume=data["volume"],
            turnover=data["turnover"],
        ).on_conflict_do_update(
            index_elements=["symbol", "period_start"],
            set_={
                "open_price": data["open_price"],
                "high_price": data["high_price"],
                "low_price": data["low_price"],
                "close_price": data["close_price"],
                "volume": data["volume"],
                "turnover": data["turnover"],
            },
        )

        return stmt

    def _aggregate_linear_instruments_klines(
        self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime
    ):
        print(f"Aggregating {timeframe} for {symbol}({start_time} -> {end_time})")
        params = self._get_klines_aggregation_params(timeframe)
        tbl = Market.ByBitLinearInstrumentsKline5m
        query = (
            select(tbl)
            .where(
                and_(
                    tbl.symbol == symbol,
                    tbl.period_start >= start_time,
                    tbl.period_start <= end_time,
                )
            )
            .order_by(tbl.period_start)
        )
        df = pd.read_sql(query, self.dbClient.connection())
        if df.shape[0] == 0:
            print("No data to aggregate for symbol: ", symbol)
            return
        df.sort_values(by="period_start", inplace=True)
        df["period_start_grouped"] = df.period_start.dt.floor(
            freq=params.pandas_freq_str
        )
        df["n_candles"] = 1
        df_grouped = (
            df.groupby("period_start_grouped")
            .agg(
                {
                    tbl.symbol.name: "first",
                    tbl.open_price.name: "first",
                    tbl.high_price.name: "max",
                    tbl.low_price.name: "min",
                    tbl.close_price.name: "last",
                    tbl.volume.name: "sum",
                    tbl.turnover.name: "sum",
                    "n_candles": "sum",
                }
            )
            .reset_index()
        )
        for _, row in df_grouped.iterrows():
            if row["n_candles"] != params.num_candles:
                print(
                    f"Issues in Candle Count: ",
                    f"Period_Start[{row['period_start_grouped']}], Symbol[{row['symbol']}]",
                    f"Count[{row['n_candles']}]",
                    params.pandas_freq_str,
                )
                continue

            stmt = self._update_insert_stmt_for_postgres(
                tbl=params.target_table,
                data_for_insert=row.to_dict(),
            )
            self.dbClient.exec(stmt)
        self.dbClient.commit()

    def aggregate_linear_instruments_klines(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        if timeframe not in ("15m", "1h", "4h", "1d") and timeframe is not None:
            print(f"Invalid Timeframe({timeframe}) for Aggregation")
            return

        # Find Timeframes to Aggregate
        timeframes_to_aggregate = []
        if timeframe is not None:
            timeframes_to_aggregate.append(timeframe)
        else:
            timeframes_to_aggregate = ["15m", "1h", "4h", "1d"]

        # Find Symbols to Aggregate
        symbols_to_aggregate = []
        if symbol is not None:
            symbols_to_aggregate.append(symbol)
        else:
            instruments = self.bb_data_service.get_linear_usdt_instruments()
            symbols_to_aggregate = [instrument.symbol for instrument in instruments]

        for symbol in symbols_to_aggregate:
            for timeframe in timeframes_to_aggregate:
                params = self._get_klines_aggregation_params(timeframe)
                latest_period_start = (
                    self.bb_data_service.get_klines_latest_period_start(
                        symbol=symbol,
                        klines_table=params.target_table,
                    )
                    or datetime(1970, 1, 1)
                )
                start_time = start_time or latest_period_start
                end_time = end_time or datetime.now()

                self._aggregate_linear_instruments_klines(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time,
                    end_time=end_time,
                )

    def aggregate_klines_by_date(self, kline_date: date, symbol: str = None):
        start_time = datetime.combine(kline_date, datetime.min.time())
        end_time = start_time + timedelta(days=1) - timedelta(seconds=1)
        self.aggregate_linear_instruments_klines(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
        )

    def process_pivot_levels(self, symbol: str):
        for timeframe in self.pivots_timeframes:
            result = self.bb_data_service.get_linear_instrument_klines(
                symbol=symbol,
                timeframe=timeframe,
                data_source="db",
            )
            data = [row.to_dict() for row in result]
            df = pd.DataFrame(data)
            for lookback in self.pivots_lookbacks:
                df["pivot"] = df.apply(
                    lambda x: pivotid(df, x.name, lookback, lookback), axis=1
                )
                for _, row in df.iterrows():
                    if row.pivot not in (1, 2):
                        continue
                    stmt = (
                        pg_insert(PriceLevels.PriceLevel)
                        .values(
                            exchange="bybit",
                            symbol=symbol,
                            instrument_type="perp",
                            timeframe=timeframe,
                            lookback_period=lookback,
                            period_start=row.period_start,
                            price_level=(
                                row.low_price if row.pivot == 1 else row.high_price
                            ),
                            is_support=row.pivot == 1,
                            is_resistance=row.pivot == 2,
                        )
                        .on_conflict_do_update(
                            index_elements=[  # unique index
                                "exchange",
                                "symbol",
                                "instrument_type",
                                "timeframe",
                                "period_start",
                                "lookback_period",
                            ],
                            set_={
                                "price_level": (
                                    row.low_price if row.pivot == 1 else row.high_price
                                ),
                                "is_support": row.pivot == 1,
                                "is_resistance": row.pivot == 2,
                            },
                        )
                    )
                    self.dbClient.exec(stmt)
        self.dbClient.commit()


class ByBitDataService:
    def __init__(self, dbClient=None):
        self.dbClient = self._get_dbClient(dbClient)
        self.redis_client = Redis(connection_pool=self._redis_connection_pool())
        self.default_client = "redis"
        self.exchange = "bybit"

    def _get_dbClient(self, dbClient):
        if dbClient is not None:
            return dbClient
        return dbOperations.get_session()

    def _redis_connection_pool(self):
        return ConnectionPool(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10,
            retry_on_timeout=True,
            max_connections=20,
        )

    def _get_kline_table(self, timeframe: str):
        if timeframe == "5m":
            return Market.ByBitLinearInstrumentsKline5m
        elif timeframe == "15m":
            return Market.ByBitLinearInstrumentsKline15m
        elif timeframe == "1h":
            return Market.ByBitLinearInstrumentsKline1h
        elif timeframe == "4h":
            return Market.ByBitLinearInstrumentsKline4h
        elif timeframe == "1d":
            return Market.ByBitLinearInstrumentsKline1d

    def get_linear_usdt_instruments(
        self, quote_coin="USDT", data_source: str = "redis"
    ):
        tbl = Market.ByBitLinearInstruments
        stmt = select(tbl).where(tbl.quote_coin == quote_coin)
        return self.dbClient.exec(stmt).all()

    def _deserialize_kline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "symbol": data["symbol"],
            "period_start": datetime.fromtimestamp(data["period_start"]),
            "open_price": Decimal(data["open_price"]),
            "high_price": Decimal(data["high_price"]),
            "low_price": Decimal(data["low_price"]),
            "close_price": Decimal(data["close_price"]),
            "volume": Decimal(data["volume"]),
            "turnover": Decimal(data["turnover"]),
        }

    def _retrive_linear_instrument_klines_from_redis(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime = None,
        end_time: datetime = None,
        output: str = "pandas",
    ):
        if start_time is None:
            start_time = datetime(1970, 1, 1)
        if end_time is None:
            end_time = datetime.now()

        start_time = int(start_time.timestamp())
        end_time = int(end_time.timestamp())
        pattern = f"bybit:kline:{timeframe}:{symbol}:*"

        keys = []
        for key in self.redis_client.scan_iter(pattern, 10000):
            current_time = int(key.split(":")[-1])
            if current_time > start_time and current_time <= end_time:
                keys.append(key)

        if keys:
            pipeline = self.redis_client.pipeline()
            for key in keys:
                pipeline.get(key)
            values = pipeline.execute()
            return sorted(
                [self._deserialize_kline(json.loads(v)) for v in values if v],
                key=lambda x: x["period_start"],
            )

    def _retrive_linear_instrument_klines_from_db(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime = None,
        end_time: datetime = None,
        output: str = "pandas",
    ):
        tbl = self._get_kline_table(timeframe)
        stmt = select(tbl).where(tbl.symbol == symbol)
        if start_time is not None:
            stmt = stmt.where(tbl.period_start >= start_time)
        if end_time is not None:
            stmt = stmt.where(tbl.period_start <= end_time)

        stmt = stmt.order_by(tbl.period_start)
        return self.dbClient.exec(stmt).all()

    def get_linear_instrument_klines(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime = None,
        end_time: datetime = None,
        data_source: str = "redis",
        output: str = "pandas",
    ):
        if data_source == "redis":
            return self._retrive_linear_instrument_klines_from_redis(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
                output=output,
            )

        return self._retrive_linear_instrument_klines_from_db(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            output=output,
        )

    def get_klines_latest_period_start(
        self,
        symbol: str,
        klines_table: SQLModel,
    ):
        tbl = klines_table
        stmt = (
            select(tbl.period_start)
            .where(tbl.symbol == symbol)
            .order_by(tbl.period_start.desc())
        )
        return self.dbClient.exec(stmt).first()

    def get_symbols_price_pivot_levels(
        self,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
        lookback_period: int = 10,
    ):
        tbl = PriceLevels.PriceLevel
        stmt = select(tbl).where(
            and_(
                tbl.exchange == self.exchange,
                tbl.symbol == symbol,
                tbl.timeframe == timeframe,
                tbl.lookback_period == lookback_period,
            )
        )
        return self.dbClient.exec(stmt).all()
