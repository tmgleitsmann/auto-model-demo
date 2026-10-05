"""Date helpers for scheduling."""

from datetime import date, timedelta


def business_days_between(start: date, end: date) -> int:
    """Count weekdays (Monday through Friday) from start to end, inclusive."""
    count = 0
    day = start
    while day <= end:
        if day.weekday() <= 5:
            count += 1
        day += timedelta(days=1)
    return count
