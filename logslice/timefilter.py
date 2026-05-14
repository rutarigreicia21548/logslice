"""Time-based filtering for log records."""

from datetime import datetime, timezone
from typing import Iterator, Optional

from logslice.parser import LogRecord, get

_TIMESTAMP_FIELDS = ("timestamp", "time", "ts", "@timestamp")
_FORMATS = (
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
)


def _parse_timestamp(value: str) -> Optional[datetime]:
    """Try to parse a timestamp string into a datetime object."""
    for fmt in _FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    try:
        ts = float(value)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (ValueError, TypeError):
        pass
    return None


def extract_timestamp(record: LogRecord) -> Optional[datetime]:
    """Extract a datetime from a log record by checking known timestamp fields."""
    for field in _TIMESTAMP_FIELDS:
        value = get(record, field)
        if value is not None:
            if isinstance(value, (int, float)):
                try:
                    return datetime.fromtimestamp(value, tz=timezone.utc)
                except (OSError, OverflowError, ValueError):
                    continue
            if isinstance(value, str):
                dt = _parse_timestamp(value)
                if dt is not None:
                    return dt
    return None


def make_time_filter(
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
):
    """Return a predicate that accepts records within the given time window."""

    def predicate(record: LogRecord) -> bool:
        dt = extract_timestamp(record)
        if dt is None:
            return True  # pass through records with no parseable timestamp
        if since is not None and dt < since:
            return False
        if until is not None and dt > until:
            return False
        return True

    return predicate


def filter_by_time(
    records: Iterator[LogRecord],
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> Iterator[LogRecord]:
    """Yield only records whose timestamp falls within [since, until]."""
    predicate = make_time_filter(since=since, until=until)
    for record in records:
        if predicate(record):
            yield record
