from datetime import datetime, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def dt(value):
    return (
        datetime.fromisoformat(value).astimezone(IST)
        if isinstance(value, str)
        else value.astimezone(IST)
    )


def utcnow():
    return datetime.now(timezone.utc)


def overlaps(start, end, other_start, other_end):
    return dt(start) < dt(other_end) and dt(other_start) < dt(end)
