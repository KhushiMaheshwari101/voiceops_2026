import csv
from datetime import datetime, date, timedelta
from typing import Set, Union
from src.config import DATA_DIR, REFERENCE_DATE


def load_holidays() -> Set[date]:
    holidays_file = DATA_DIR / "holidays.csv"
    holiday_set = set()
    if holidays_file.exists():
        with open(holidays_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                d_str = row.get("date", "").strip()
                if d_str:
                    try:
                        holiday_set.add(datetime.strptime(d_str, "%Y-%m-%d").date())
                    except ValueError:
                        pass
    return holiday_set


HOLIDAYS = load_holidays()
REF_DATE = datetime.strptime(REFERENCE_DATE, "%Y-%m-%d").date()


def parse_date(d: Union[str, date]) -> date:
    if isinstance(d, date):
        return d
    return datetime.strptime(str(d).strip(), "%Y-%m-%d").date()


def is_business_day(d: date) -> bool:
    # Business day: Mon-Sat (weekday 0-5), excluding holidays
    if d.weekday() == 6:  # Sunday
        return False
    if d in HOLIDAYS:
        return False
    return True


def add_business_days(start_date: Union[str, date], n: int) -> date:
    cur = parse_date(start_date)
    added = 0
    while added < n:
        cur += timedelta(days=1)
        if is_business_day(cur):
            added += 1
    return cur


def add_calendar_days(start_date: Union[str, date], n: int) -> date:
    cur = parse_date(start_date)
    return cur + timedelta(days=n)


def format_date_for_chat(d: Union[str, date]) -> str:
    dt = parse_date(d)
    return dt.strftime("%d %B %Y").lstrip("0")


def format_date_for_speech(d: Union[str, date]) -> str:
    dt = parse_date(d)
    day = dt.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"the {day}{suffix} of {dt.strftime('%B %Y')}"
