from sqlmodel import and_, select, text
from xchanges.ByBit import MarketData, Category, Interval, ContractType
from database.models import Market
from database import Operations as dbOperations
from datetime import datetime, date, timedelta
import time


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

    def process_linear_instruments_klines(self) -> None:
        """Process klines using direct SQL operations for maximum performance"""
        start_time = time.time()
        total_processed = 0

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
