from datetime import datetime, timedelta
from typing import Optional, Tuple
import pandas as pd


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def parse_dates(
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[datetime.date, datetime.date]:
    if end_date and not start_date:
        start_date = end_date
    if start_date and not end_date:
        end_date = datetime.today().date().strftime("%Y-%m-%d")

    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    return start_date, end_date


def pivotid(df: pd.DataFrame, l: int, n1: int, n2: int) -> int:
    """
    Identify pivot points in the data
    Returns:
        0: Not a pivot
        1: Support (pivot low)
        2: Resistance (pivot high)
        3: Both support and resistance
    """
    if l - n1 < 0 or l + n2 >= len(df):
        return 0

    pividlow = 1
    pividhigh = 1
    for i in range(l - n1, l + n2 + 1):
        if df.iloc[l]["low_price"] > df.iloc[i]["low_price"]:
            pividlow = 0
        if df.iloc[l]["high_price"] < df.iloc[i]["high_price"]:
            pividhigh = 0

    if pividlow and pividhigh:
        return 3
    elif pividlow:
        return 1
    elif pividhigh:
        return 2
    else:
        return 0
