from sqlmodel import and_, select, text, insert, SQLModel
from xchanges.ByBit import MarketData, Category, Interval, ContractType
from database.models import Market
from database.models.Market import Timeframe
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database import Operations as dbOperations
from datetime import datetime, date, timedelta
import time
from typing import Optional
import pandas as pd


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
        kline_date: date = None,
    ):
        downloaded_at = int(datetime.now().timestamp())
        # if kline_date is None then fetch last 5 mins
        if kline_date is None:
            current_time = datetime.now()
            end_time = current_time
            start_time = current_time - timedelta(minutes=5)
        else:
            start_time = datetime.combine(kline_date, datetime.min.time())
            end_time = start_time + timedelta(days=1) - timedelta(seconds=1)

        instruments = self.get_current_linear_instruments("USDT")
        for instrument in instruments:
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

    def process_linear_instruments_klines(self, kline_date=None) -> None:
        # Download klines if kline_date is provided
        self.download_linear_instruments_klines_to_db(kline_date=kline_date)

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
        ON CONFLICT (symbol, period_start) DO NOTHING
        RETURNING 1;
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
    ):
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
        df = pd.read_sql(query, self.dbClient.connection())
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
                .on_conflict_do_nothing(index_elements=["symbol", "period_start"])
            )
            self.dbClient.exec(stmt)
        self.dbClient.commit()

    def aggregate_linear_instrument_klines_to_15m(self, symbol: str):
        print("Aggregating 5m to 15m for symbol: ", symbol)
        tbl_5m = Market.ByBitLinearInstrumentsKline5m
        tbl_15m = Market.ByBitLinearInstrumentsKline15m
        self.aggregate_linear_instrument_klines_from_and_to_timeframe(
            symbol=symbol,
            source_table=tbl_5m,
            target_table=tbl_15m,
            freq_str="15min",
            n_candles=3,
        )

    def aggregate_linear_instrument_klines_to_1h(self, symbol: str):
        print("Aggregating 15m to 1h for symbol: ", symbol)
        tbl_15m = Market.ByBitLinearInstrumentsKline15m
        tbl_1h = Market.ByBitLinearInstrumentsKline1h
        self.aggregate_linear_instrument_klines_from_and_to_timeframe(
            symbol=symbol,
            source_table=tbl_15m,
            target_table=tbl_1h,
            freq_str="1h",
            n_candles=4,
        )

    def aggregate_linear_instrument_klines_to_4h(self, symbol: str):
        print("Aggregating 1h to 4h for symbol: ", symbol)
        tbl_1h = Market.ByBitLinearInstrumentsKline1h
        tbl_4h = Market.ByBitLinearInstrumentsKline4h
        self.aggregate_linear_instrument_klines_from_and_to_timeframe(
            symbol=symbol,
            source_table=tbl_1h,
            target_table=tbl_4h,
            freq_str="4h",
            n_candles=4,
        )

    def aggregate_linear_instrument_klines_to_1d(self, symbol: str):
        print("Aggregating 4h to 1d for symbol: ", symbol)
        tbl_4h = Market.ByBitLinearInstrumentsKline4h
        tbl_1d = Market.ByBitLinearInstrumentsKline1d
        self.aggregate_linear_instrument_klines_from_and_to_timeframe(
            symbol=symbol,
            source_table=tbl_4h,
            target_table=tbl_1d,
            freq_str="D",
            n_candles=6,
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

    def aggregate_linear_instrument_klines(
        self,
        symbol: str,
    ) -> None:
        self.aggregate_linear_instrument_klines_to_15m(symbol=symbol)
        self.aggregate_linear_instrument_klines_to_1h(symbol=symbol)
        self.aggregate_linear_instrument_klines_to_4h(symbol=symbol)
        self.aggregate_linear_instrument_klines_to_1d(symbol=symbol)

    def aggregate_linear_instruments_klines(
        self,
        symbol: str = None,
    ) -> None:
        symbols_to_aggregate = []
        if symbol is not None:
            symbols_to_aggregate.append(symbol)
        else:
            instruments = self.get_current_linear_instruments("USDT")
            symbols_to_aggregate = [instrument.symbol for instrument in instruments]

        for symbol in symbols_to_aggregate:
            print("Processing symbol: ", symbol)
            self.aggregate_linear_instrument_klines(symbol=symbol)

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
            end_date = end_date - timedelta(minutes=end_date.minute % 5)

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

        return missing_periods
