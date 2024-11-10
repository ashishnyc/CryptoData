from datetime import datetime, timedelta
from typing import Optional, Tuple


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
