import asyncio
from collections import defaultdict
from decimal import Decimal
import json
from sqlmodel import Session, and_, select, text, insert, SQLModel, func
from xchanges.ByBit import MarketData, Category, Interval, ContractType
from database.models import Market
from database.models.Market import Timeframe
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database import Operations as dbOperations
from datetime import datetime, date, timedelta
import time
from typing import Any, Dict, Optional
import pandas as pd
from redis import ConnectionPool, Redis
from sqlmodel.ext.asyncio.session import AsyncSession


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

    def download_linear_instrument_klines(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        # Determine Parameters for Fetching Klines
        start_time = start_time or (datetime.now() - timedelta(minutes=15))
        end_time = end_time or datetime.now()

        params = {
            "category": Category.LINEAR,
            "symbol": symbol,
            "interval": self.default_interval,
            "start_time": start_time,
            "end_time": end_time,
        }

        process_start_time = time.time()

        klines = self.client.fetch_kline(**params)

        if not klines:
            print(f"No klines found for {symbol}")
            return

        # Process Klines
        processed_klines = []
        for kline in klines:
            new_kline = Market.ByBitLinearInstrumentsKline5m()
            new_kline.set_symbol(symbol)
            new_kline.set_period_start(kline[0])
            new_kline.set_open_price(kline[1])
            new_kline.set_high_price(kline[2])
            new_kline.set_low_price(kline[3])
            new_kline.set_close_price(kline[4])
            new_kline.set_volume(kline[5])
            new_kline.set_turnover(kline[6])
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
        to_update = []
        to_create = []

        for kline in processed_klines:
            key = (kline.symbol, kline.period_start)
            existing = existing_records.get(key)
            if existing:
                # Skip if existing record is the same
                if existing.is_equal(kline):
                    continue
                # Update existing record
                existing.open_price = kline.open_price
                existing.high_price = kline.high_price
                existing.low_price = kline.low_price
                existing.close_price = kline.close_price
                existing.volume = kline.volume
                existing.turnover = kline.turnover
                to_update.append(existing)
            else:
                to_create.append(kline)

        try:
            # Bulk save updates
            if to_update:
                self.dbClient.bulk_save_objects(to_update)

            # Bulk create new records
            if to_create:
                self.dbClient.bulk_save_objects(to_create)

            self.dbClient.commit()

            duration = time.time() - process_start_time
            total_processed = len(to_update) + len(to_create)
            print(f"Updated: {len(to_update)}, Created: {len(to_create)}")
            print(f"Processing speed: {total_processed/duration:.2f} records/second")

        except Exception as e:
            self.dbClient.rollback()
            print(f"Database error for {symbol}: {e}")
            raise


class ByBitDataService:
    def __init__(self, dbClient=None):
        self.dbClient = self._get_dbClient(dbClient)
        self.redis_client = Redis(connection_pool=self._redis_connection_pool())
        self.default_client = "redis"

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
    ):
        tbl = self._get_kline_table(timeframe)
        stmt = select(tbl).where(tbl.symbol == symbol)
        if start_time is not None:
            stmt = stmt.where(tbl.period_start >= start_time)
        if end_time is not None:
            stmt = stmt.where(tbl.period_start <= end_time)
        return self.dbClient.exec(stmt).all()

    def get_linear_instrument_klines(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime = None,
        end_time: datetime = None,
        data_source: str = "redis",
    ):
        if data_source == "redis":
            return self._retrive_linear_instrument_klines_from_redis(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
            )

        return self._retrive_linear_instrument_klines_from_db(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
        )


class ByBitMarketDataManager:
    def __init__(
        self, testnet: bool = False, api_key: str = None, api_secret: str = None
    ):
        self.dbClient = dbOperations.get_session()

        self.client = MarketData(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret,
        )
        self.default_interval = Interval._5_MIN
        self.db_processing_batch_size = 10000

    def get_linear_instruments_downloaded_ts(
        self,
        contract_type: str,
        quote_coin: str,
        download_ts: int,
    ):
        """
        Retrieves the most recent downloaded timestamp for ByBit instruments
        that match the given contract type and quote coin, and are older than
        the specified download timestamp.

        Args:
            contract_type (str): The type of contract (e.g., 'perpetual', 'futures').
            quote_coin (str): The quote currency (e.g., 'USD', 'BTC').
            download_ts (int): The download timestamp to compare against.

        Returns:
            sqlalchemy.engine.Row: The row containing the most recent downloaded timestamp
            that matches the criteria, or None if no such timestamp exists.
        """
        stmt = (
            select(Market.ByBitInstrumentsRaw.downloaded_at)
            .where(
                and_(
                    Market.ByBitInstrumentsRaw.contract_type == contract_type,
                    Market.ByBitInstrumentsRaw.quote_coin == quote_coin,
                    Market.ByBitInstrumentsRaw.downloaded_at < download_ts,
                )
            )
            .order_by(Market.ByBitInstrumentsRaw.downloaded_at.desc())
        )
        return self.dbClient.exec(stmt).first()

    def get_downloaded_linear_instruments(
        self,
        contract_type: str,
        quote_coin: str,
        download_ts: int,
    ):
        stmt = select(Market.ByBitInstrumentsRaw).where(
            and_(
                Market.ByBitInstrumentsRaw.contract_type == contract_type,
                Market.ByBitInstrumentsRaw.quote_coin == quote_coin,
                Market.ByBitInstrumentsRaw.downloaded_at == download_ts,
            )
        )
        return self.dbClient.exec(stmt).all()

    def get_latest_downloaded_linear_instruments(
        self,
        contract_type: str,
        quote_coin: str,
    ):
        """
        Retrieves downloaded instrument data from the ByBit market.
        Args:
            contract_type (str): The type of contract (e.g., 'perpetual', 'futures').
            quote_coin (str): The quote currency (e.g., 'USD', 'BTC').
            download_ts (int): The timestamp when the data was downloaded.
        Returns:
            List[Market.ByBitInstrumentsRaw]: A list of ByBit instrument data records matching the specified criteria.
        """
        latest_ts = self.get_linear_instruments_downloaded_ts(
            contract_type=contract_type,
            quote_coin=quote_coin,
            download_ts=datetime.now().timestamp(),
        )

        return self.get_downloaded_linear_instruments(
            contract_type=contract_type,
            quote_coin=quote_coin,
            download_ts=latest_ts,
        )

    def get_current_linear_instruments(
        self,
        quote_coin: str,
    ):
        stmt = select(Market.ByBitLinearInstruments).where(
            and_(
                Market.ByBitLinearInstruments.quote_coin == quote_coin,
            )
        )
        return self.dbClient.exec(stmt).all()

    def process_linear_perpetual_usdt(
        self,
        contract_type: str = ContractType.LINEAR_PERPETUAL.value,
        quote_coin: str = "USDT",
    ):
        # Download Linear Category Instruments
        self.download_instruments_to_db(category=Category.LINEAR)

        # Fetch current data
        current_instruments = self.get_current_linear_instruments(quote_coin=quote_coin)
        current_instruments_map = {
            instrument.symbol: instrument for instrument in current_instruments
        }

        # Fetch latest downloaded data
        new_instruments = self.get_latest_downloaded_linear_instruments(
            contract_type=contract_type, quote_coin=quote_coin
        )
        new_instruments_map = {
            instrument.symbol: instrument for instrument in new_instruments
        }

        inserts, updates, deletes = 0, 0, 0
        for new_instrument in new_instruments:
            instrument_data = {
                "symbol": new_instrument.symbol,
                "base_coin": new_instrument.base_coin,
                "quote_coin": new_instrument.quote_coin,
                "launch_time": new_instrument.launch_time,
                "price_scale": new_instrument.price_scale,
                "funding_interval": new_instrument.funding_interval,
                "min_leverage": new_instrument.min_leverage,
                "max_leverage": new_instrument.max_leverage,
                "leverage_step": new_instrument.leverage_step,
                "max_trading_qty": new_instrument.max_trading_qty,
                "min_trading_qty": new_instrument.min_trading_qty,
                "qty_step": new_instrument.qty_step,
                "min_price": new_instrument.min_price,
                "max_price": new_instrument.max_price,
                "tick_size": new_instrument.tick_size,
            }
            existing_instrument = current_instruments_map.get(new_instrument.symbol)

            if existing_instrument:
                has_changed = False
                for key, value in instrument_data.items():
                    if getattr(existing_instrument, key) != value:
                        has_changed = True
                        setattr(existing_instrument, key, value)

                if has_changed:
                    updates += 1
                    self.dbClient.add(existing_instrument)
            else:
                new_instrument = Market.ByBitLinearInstruments(**instrument_data)
                self.dbClient.add(new_instrument)
                inserts += 1
        for symbol in current_instruments_map:
            if symbol not in new_instruments_map:
                self.dbClient.delete(current_instruments_map[symbol])
                deletes += 1
        self.dbClient.commit()
        print(
            f"Processed linear perpetual USDT instruments: {inserts} inserts, {updates} updates, {deletes} deletes"
        )

    def download_instruments_to_db(self, category: Category, limit: int = None):
        instruments = self.client.fetch_instruments(category, limit)
        downloaded_at = int(datetime.now().timestamp())
        for instrument in instruments:
            instrument["downloaded_at"] = downloaded_at
            new_instrument = Market.ByBitInstrumentsRaw()
            new_instrument.process_xchange_info(instrument)
            self.dbClient.add(new_instrument)
        self.dbClient.commit()

    def download_linear_instrument_symbol_klines_to_db(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        download_ts: int,
        commit_to_db: bool = False,
    ):

        params = {
            "category": Category.LINEAR,
            "symbol": symbol,
            "interval": self.default_interval,
            "start_time": start_time,
            "end_time": end_time,
        }
        klines = self.client.fetch_kline(**params)
        for kline in klines:
            print(kline)
            new_kline = Market.ByBitLinearInstrumentsKline5mRaw()
            new_kline.downloaded_at = download_ts
            new_kline.symbol = symbol
            new_kline.startTime = kline[0]
            new_kline.openPrice = kline[1]
            new_kline.highPrice = kline[2]
            new_kline.lowPrice = kline[3]
            new_kline.closePrice = kline[4]
            new_kline.volume = kline[5]
            new_kline.turnover = kline[6]
            self.dbClient.add(new_kline)
        if commit_to_db:
            self.dbClient.commit()

    def download_linear_instruments_klines_to_db(
        self,
        symbol: str = None,
        kline_date: date = None,
    ):
        downloaded_at = int(datetime.now().timestamp())
        # if kline_date is None then fetch last 15 mins (just for making sure we have the latest data)
        if kline_date is None:
            current_time = datetime.now()
            end_time = current_time
            start_time = current_time - timedelta(minutes=15)
        else:
            start_time = datetime.combine(kline_date, datetime.min.time())
            end_time = start_time + timedelta(days=1) - timedelta(seconds=1)

        instruments = self.get_current_linear_instruments("USDT")
        for instrument in instruments:
            if symbol is not None and instrument.symbol != symbol:
                continue
            if instrument.launch_time < int(end_time.timestamp()):
                self.download_linear_instrument_symbol_klines_to_db(
                    symbol=instrument.symbol,
                    start_time=start_time,
                    end_time=end_time,
                    download_ts=downloaded_at,
                )
        self.dbClient.commit()

    def get_unprocessed_linear_instruments_klines_raw(self):
        stmt = (
            select(Market.ByBitLinearInstrumentsKline5mRaw)
            .where(Market.ByBitLinearInstrumentsKline5mRaw.is_processed == False)
            .limit(self.db_processing_batch_size)
        )
        return self.dbClient.exec(stmt).all()

    def process_linear_instruments_klines_v0(self):
        total_processed = 0
        while True:
            unprocessed_klines = self.get_unprocessed_linear_instruments_klines_raw()
            if len(unprocessed_klines) == 0:
                break

            processed_klines = []
            raw_klines_to_update = []

            for unprocessed_kline in unprocessed_klines:
                new_kline = Market.ByBitLinearInstrumentsKline5m()
                new_kline.symbol = unprocessed_kline.symbol
                new_kline.period_start = datetime.fromtimestamp(
                    int(unprocessed_kline.startTime) / 1000
                )
                new_kline.open_price = unprocessed_kline.openPrice
                new_kline.high_price = unprocessed_kline.highPrice
                new_kline.low_price = unprocessed_kline.lowPrice
                new_kline.close_price = unprocessed_kline.closePrice
                new_kline.volume = unprocessed_kline.volume
                new_kline.turnover = unprocessed_kline.turnover
                unprocessed_kline.is_processed = True

                # update list of processed klines
                processed_klines.append(new_kline)
                raw_klines_to_update.append(unprocessed_kline)

            try:
                # Bulk Save All Processed Klines
                self.dbClient.bulk_save_objects(processed_klines)

                # Bulk Update All Raw Klines
                self.dbClient.bulk_save_objects(raw_klines_to_update)
                self.dbClient.commit()
                total_processed += len(unprocessed_klines)

                print(f"Processed {total_processed} klines")
            except Exception as e:
                print(f"Error saving batch: {e}")
                self.dbClient.rollback()
                continue
        print(f"Total processed: {total_processed}")

    def process_linear_instruments_klines(self, symbol=None, kline_date=None) -> None:
        # Download klines if kline_date is provided
        self.download_linear_instruments_klines_to_db(
            symbol=symbol, kline_date=kline_date
        )

        start_time = time.time()

        # Direct SQL for better performance while maintaining SQLModel table names
        insert_query = f"""
        INSERT INTO {Market.ByBitLinearInstrumentsKline5m.__tablename__} 
            (symbol, period_start, open_price, high_price, low_price, close_price, volume, turnover)
        SELECT 
            symbol,
            to_timestamp(CAST(CAST("startTime" AS BIGINT) / 1000 AS INTEGER)) as period_start,
            CAST("openPrice" AS DECIMAL(38,8)),
            CAST("highPrice" AS DECIMAL(38,8)),
            CAST("lowPrice" AS DECIMAL(38,8)),
            CAST("closePrice" AS DECIMAL(38,8)),
            CAST(volume AS DECIMAL(38,8)),
            CAST(turnover AS DECIMAL(38,8))
        FROM {Market.ByBitLinearInstrumentsKline5mRaw.__tablename__}
        WHERE is_processed = FALSE
        ON CONFLICT (symbol, period_start)
        DO UPDATE SET
            open_price = EXCLUDED.open_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume,
            turnover = EXCLUDED.turnover
        """

        # Update processed status
        update_query = f"""
        UPDATE {Market.ByBitLinearInstrumentsKline5mRaw.__tablename__}
        SET is_processed = TRUE
        WHERE is_processed = FALSE;
        """

        try:
            # Execute insert
            result = self.dbClient.exec(text(insert_query))
            rows_inserted = result.rowcount

            # Execute update
            self.dbClient.exec(text(update_query))

            # Commit transaction
            self.dbClient.commit()

            end_time = time.time()
            duration = end_time - start_time

            print(f"Processed {rows_inserted} records in {duration:.2f} seconds")
            print(f"Processing speed: {rows_inserted/duration:.2f} records/second")

        except Exception as e:
            self.dbClient.rollback()
            print(f"Error during processing: {e}")
            raise

    def get_linear_instruments_klines(self, symbol: str, timeframe: None):
        if timeframe is None or timeframe == "5m":
            tbl_kline = Market.ByBitLinearInstrumentsKline5m
        elif timeframe == "15m":
            tbl_kline = Market.ByBitLinearInstrumentsKline15m
        elif timeframe == "1h":
            tbl_kline = Market.ByBitLinearInstrumentsKline1h
        elif timeframe == "4h":
            tbl_kline = Market.ByBitLinearInstrumentsKline4h
        elif timeframe == "1d":
            tbl_kline = Market.ByBitLinearInstrumentsKline1d
        stmt = (
            select(tbl_kline)
            .where(tbl_kline.symbol == symbol)
            .order_by(tbl_kline.period_start)
        )
        return self.dbClient.exec(stmt).all()

    def aggregate_linear_instrument_klines_from_and_to_timeframe(
        self,
        symbol: str,
        source_table,
        target_table,
        freq_str,
        n_candles,
        kline_date=None,
    ):
        if kline_date is None:
            last_period_start_in_source = (
                self.get_linear_instruments_klines_latest_period_start(
                    symbol=symbol, klines_table=target_table
                )
            )
            query = select(source_table).where(
                and_(
                    source_table.symbol == symbol,
                    source_table.period_start >= last_period_start_in_source,
                )
            )
        else:
            query = select(source_table).where(
                and_(
                    source_table.symbol == symbol,
                    func.date(source_table.period_start) == kline_date,
                )
            )
        df = pd.read_sql(query, self.dbClient.connection())
        if df.shape[0] == 0:
            print("No data to aggregate for symbol: ", symbol)
            return
        df.sort_values(by="period_start", inplace=True)
        df["period_start_grouped"] = df.period_start.dt.floor(freq=freq_str)
        df["n_candles"] = 1
        df_grouped = (
            df.groupby("period_start_grouped")
            .agg(
                {
                    source_table.symbol.name: "first",
                    source_table.open_price.name: "first",
                    source_table.high_price.name: "max",
                    source_table.low_price.name: "min",
                    source_table.close_price.name: "last",
                    source_table.volume.name: "sum",
                    source_table.turnover.name: "sum",
                    "n_candles": "sum",
                }
            )
            .reset_index()
        )
        for _, row in df_grouped.iterrows():
            if row["n_candles"] != n_candles:
                print(
                    f"Issues in Candle Count: ",
                    f"Period_Start[{row['period_start_grouped']}], Symbol[{row['symbol']}]",
                    f"Count[{row['n_candles']}]",
                    freq_str,
                )
                continue
            stmt = (
                pg_insert(target_table)
                .values(
                    symbol=row["symbol"],
                    period_start=row["period_start_grouped"],
                    open_price=row["open_price"],
                    high_price=row["high_price"],
                    low_price=row["low_price"],
                    close_price=row["close_price"],
                    volume=row["volume"],
                    turnover=row["turnover"],
                )
                .on_conflict_do_update(
                    index_elements=["symbol", "period_start"],
                    set_={
                        "open_price": row["open_price"],
                        "high_price": row["high_price"],
                        "low_price": row["low_price"],
                        "close_price": row["close_price"],
                        "volume": row["volume"],
                        "turnover": row["turnover"],
                    },
                )
            )
            self.dbClient.exec(stmt)
        self.dbClient.commit()

    def aggregate_linear_instrument_klines_to_15m(self, symbol: str, kline_date=None):
        print("Aggregating 5m to 15m for symbol: ", symbol)
        tbl_5m = Market.ByBitLinearInstrumentsKline5m
        tbl_15m = Market.ByBitLinearInstrumentsKline15m
        self.aggregate_linear_instrument_klines_from_and_to_timeframe(
            symbol=symbol,
            source_table=tbl_5m,
            target_table=tbl_15m,
            freq_str="15min",
            n_candles=3,
            kline_date=kline_date,
        )

    def aggregate_linear_instrument_klines_to_1h(self, symbol: str, kline_date=None):
        print("Aggregating 15m to 1h for symbol: ", symbol)
        tbl_15m = Market.ByBitLinearInstrumentsKline15m
        tbl_1h = Market.ByBitLinearInstrumentsKline1h
        self.aggregate_linear_instrument_klines_from_and_to_timeframe(
            symbol=symbol,
            source_table=tbl_15m,
            target_table=tbl_1h,
            freq_str="1h",
            n_candles=4,
            kline_date=kline_date,
        )

    def aggregate_linear_instrument_klines_to_4h(self, symbol: str, kline_date=None):
        print("Aggregating 1h to 4h for symbol: ", symbol)
        tbl_1h = Market.ByBitLinearInstrumentsKline1h
        tbl_4h = Market.ByBitLinearInstrumentsKline4h
        self.aggregate_linear_instrument_klines_from_and_to_timeframe(
            symbol=symbol,
            source_table=tbl_1h,
            target_table=tbl_4h,
            freq_str="4h",
            n_candles=4,
            kline_date=kline_date,
        )

    def aggregate_linear_instrument_klines_to_1d(self, symbol: str, kline_date=None):
        print("Aggregating 4h to 1d for symbol: ", symbol)
        tbl_4h = Market.ByBitLinearInstrumentsKline4h
        tbl_1d = Market.ByBitLinearInstrumentsKline1d
        self.aggregate_linear_instrument_klines_from_and_to_timeframe(
            symbol=symbol,
            source_table=tbl_4h,
            target_table=tbl_1d,
            freq_str="D",
            n_candles=6,
            kline_date=kline_date,
        )

    def get_linear_instruments_klines_latest_period_start(
        self, symbol: str, klines_table
    ):
        if klines_table is None:
            return None
        tbl = klines_table
        if tbl.__tablename__.startswith("bybit_linear_instruments_kline"):
            return None
        stmt = (
            select(tbl.period_start)
            .where(tbl.symbol == symbol)
            .order_by(tbl.period_start.desc())
            .limit(1)
        )
        value = self.dbClient.exec(stmt).first()
        if value is None:
            return datetime(1970, 1, 1)
        return value

    def aggregate_linear_instrument_klines(self, symbol: str, kline_date=None) -> None:
        self.aggregate_linear_instrument_klines_to_15m(
            symbol=symbol, kline_date=kline_date
        )
        self.aggregate_linear_instrument_klines_to_1h(
            symbol=symbol, kline_date=kline_date
        )
        self.aggregate_linear_instrument_klines_to_4h(
            symbol=symbol, kline_date=kline_date
        )
        self.aggregate_linear_instrument_klines_to_1d(
            symbol=symbol, kline_date=kline_date
        )

    def aggregate_linear_instruments_klines(self, kline_date=None, symbol=None) -> None:
        symbols_to_aggregate = []
        if symbol is not None:
            symbols_to_aggregate.append(symbol)
        else:
            instruments = self.get_current_linear_instruments("USDT")
            symbols_to_aggregate = [instrument.symbol for instrument in instruments]

        for symbol in symbols_to_aggregate:
            print("Processing symbol: ", symbol)
            self.aggregate_linear_instrument_klines(
                symbol=symbol, kline_date=kline_date
            )

    def get_missing_kline_periods(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[datetime]:
        """
        Check for missing 5-minute candles in the time series data.

        Args:
            symbol (str): The trading pair symbol to check
            start_date (datetime, optional): Start date to check from. If None, uses first available candle
            end_date (datetime, optional): End date to check until. If None, uses current time

        Returns:
            list[datetime]: List of datetime objects representing missing periods
        """
        # Get all existing candles for the symbol
        tbl_kline = Market.ByBitLinearInstrumentsKline5m

        # Build base query
        query = select(tbl_kline.period_start).where(tbl_kline.symbol == symbol)

        # Add date filters if provided
        if start_date:
            query = query.where(tbl_kline.period_start >= start_date)
        if end_date:
            query = query.where(tbl_kline.period_start <= end_date)

        # Order by period start
        query = query.order_by(tbl_kline.period_start)

        # Execute query and get all timestamps
        existing_periods = self.dbClient.exec(query).all()

        if not existing_periods:
            return []

        # If start_date not provided, use first available candle
        if not start_date:
            start_date = existing_periods[0]

        # If end_date not provided, use current time rounded down to nearest 5 minutes
        if not end_date:
            end_date = datetime.now().replace(second=0, microsecond=0)
            end_date = end_date - timedelta(days=1)

        # Generate all expected 5-minute periods
        expected_periods = []
        current_period = start_date
        while current_period <= end_date:
            expected_periods.append(current_period)
            current_period += timedelta(minutes=5)

        # Convert existing periods to set for O(1) lookup
        existing_periods_set = set(existing_periods)

        # Find missing periods
        missing_periods = [
            period for period in expected_periods if period not in existing_periods_set
        ]
        missing_dates = set([period.date() for period in missing_periods])
        return missing_dates


class ByBitKlineCache:
    def __init__(
        self, redis_client: Redis, refresh_interval: int = 300, max_age_hours: int = 24
    ):
        self.redis_client = redis_client
        self.refresh_interval = refresh_interval
        self.max_age_hours = max_age_hours

        # Aditional Initialization
        self.background_task = None
        self.is_running = False
        self._last_updates = defaultdict(lambda: datetime.min)

    def get_cache_key(self, symbol: str, period_start: datetime, tf: str = "5m") -> str:
        return f"bybit:kline:{tf}:{symbol}:{int(period_start.timestamp())}"

    def serialize_kline(self, kline) -> Dict[str, Any]:
        return {
            "symbol": kline.symbol,
            "period_start": kline.period_start.timestamp(),
            "open_price": str(kline.open_price),
            "high_price": str(kline.high_price),
            "low_price": str(kline.low_price),
            "close_price": str(kline.close_price),
            "volume": str(kline.volume),
            "turnover": str(kline.turnover),
        }

    def deserialize_kline(self, data: Dict[str, Any]) -> Dict[str, Any]:
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

    async def start_background_refresh(self, engine):
        if self.is_running:
            return
        self.is_running = True
        self.background_task = asyncio.create_task(
            self._background_refresh_loop(engine)
        )

    async def stop_background_refresh(self):
        if self.background_task:
            self.background_task.cancel()
            self.is_running = False
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass

    async def _background_refresh_loop(self, engine):
        while self.is_running:
            try:
                async with AsyncSession(engine) as session:
                    tbl = Market.ByBitLinearInstruments
                    query = select(tbl.symbol).where(tbl.quote_coin == "USDT")
                    symbols = (await session.exec(query)).all()
                    symbols = ["BTCUSDT"]
                    for symbol in symbols:
                        await self._refresh_symbol_data(session, symbol)
            except Exception as e:
                print(f"Error during background refresh: {e}")
                await asyncio.sleep(10)

    async def _refresh_symbol_data(self, session, symbol: str):
        now = datetime.now()
        if (now - self._last_updates[symbol]).total_seconds() < self.refresh_interval:
            return

        tbl = Market.ByBitLinearInstrumentsKline5m
        query = (
            select(tbl).where(tbl.symbol == symbol)
            # .where(tbl.period_start >= (now - timedelta(days=14)))
        )
        klines = (await session.exec(query)).all()
        if not klines:
            return

        pipeline = self.redis_client.pipeline()
        for kline in klines:
            serialized_kline = self.serialize_kline(kline)
            key_5m = self.get_cache_key(kline.symbol, kline.period_start)
            pipeline.set(key_5m, json.dumps(serialized_kline))

        pipeline.execute()

        self._last_updates[symbol] = now

    def get_kline(self, symbol: str, tf: str = "5m") -> Dict[str, Any]:
        pattern = f"bybit:kline:{tf}:{symbol}:*"
        keys = []

        for key in self.redis_client.scan_iter(pattern, 1000):
            keys.append(key)

        if keys:
            pipeline = self.redis_client.pipeline()
            for key in keys:
                pipeline.get(key)
            values = pipeline.execute()
            return sorted(
                [self.deserialize_kline(json.loads(v)) for v in values if v],
                key=lambda x: x["period_start"],
            )
        return []
