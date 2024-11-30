import argparse
from dataManagers.ByBitMarketDataManager import ByBitMarketDataManager
import utils


def main(symbol=None, start_date=None, end_date=None):
    bb = ByBitMarketDataManager()
    if start_date or end_date:
        start_date, end_date = utils.parse_dates(start_date, end_date)
        for single_date in utils.daterange(start_date, end_date):
            print(f"running for {single_date}")
            bb.process_linear_instruments_klines(symbol=symbol, kline_date=single_date)
            bb.aggregate_linear_instruments_klines(
                symbol=symbol, kline_date=single_date
            )

    else:
        bb.process_linear_perpetual_usdt()
        bb.process_linear_instruments_klines()
        bb.aggregate_linear_instruments_klines()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and process ByBit market data."
    )
    parser.add_argument("--start_date", type=str, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end_date", type=str, help="End date in YYYY-MM-DD")
    parser.add_argument("--symbol", type=str, help="Symbol to download")

    args = parser.parse_args()

    main(symbol=args.symbol, start_date=args.start_date, end_date=args.end_date)
