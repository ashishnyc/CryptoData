import argparse
from dataManagers.ByBitMarketDataManager import ByBitMarketDataManager
from xchanges.ByBit import Category
from datetime import datetime, timedelta


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def main(start_date=None, end_date=None):
    bb = ByBitMarketDataManager()
    if start_date or end_date:
        if end_date and not start_date:
            start_date = end_date
        if start_date and not end_date:
            end_date = datetime.today().date().strftime("%Y-%m-%d")

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        for single_date in daterange(start_date, end_date):
            print(f"running for {single_date}")
            bb.download_linear_instruments_klines_to_db(kline_date=single_date)
            bb.process_linear_instruments_klines()

    else:
        bb.download_instruments_to_db(category=Category.LINEAR)
        bb.process_linear_perpetual_usdt()
        bb.download_linear_instruments_klines_to_db()
        bb.process_linear_instruments_klines()


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
