"""Delhi-NCR business dates; retain naive UTC timestamps in legacy DB columns."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

INDIA = ZoneInfo("Asia/Kolkata")


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def localdate():
    return datetime.now(INDIA).date()


def india_date(value):
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(INDIA).strftime("%d %b %Y")
