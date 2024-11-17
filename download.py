import argparse
from dataManagers.ByBitMarketDataManager import ByBitMarketDataManager
import utils


def main(start_date=None, end_date=None):
    bb = ByBitMarketDataManager()
    if start_date or end_date:
        start_date, end_date = utils.parse_dates(start_date, end_date)
        for single_date in utils.daterange(start_date, end_date):
            print(f"running for {single_date}")
            bb.process_linear_instruments_klines(kline_date=single_date)
            bb.aggregate_linear_instruments_klines()

    else:
        bb.process_linear_perpetual_usdt()
        bb.process_linear_instruments_klines()
        bb.aggregate_linear_instruments_klines()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and process ByBit market data."
    )
    parser.add_argument(
        "--start_date", type=str, help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument("--end_date", type=str, help="End date in YYYY-MM-DD format")
    args = parser.parse_args()

    main(start_date=args.start_date, end_date=args.end_date)
