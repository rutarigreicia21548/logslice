"""Field value truncation for long log messages."""

from typing import Iterator, Optional
from logslice.parser import LogRecord, get


DEFAULT_MAX_LENGTH = 200
_ELLIPSIS = "..."


def truncate_value(value: str, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """Truncate a string value to max_length, appending ellipsis if trimmed."""
    if not isinstance(value, str):
        return value
    if len(value) <= max_length:
        return value
    cut = max(0, max_length - len(_ELLIPSIS))
    return value[:cut] + _ELLIPSIS


def truncate_field(
    record: LogRecord,
    field: str,
    max_length: int = DEFAULT_MAX_LENGTH,
) -> LogRecord:
    """Return a new LogRecord with the named field truncated."""
    value = get(record, field)
    if value is None or not isinstance(value, str):
        return record
    truncated = truncate_value(value, max_length)
    if truncated == value:
        return record
    new_data = dict(record.data) if record.data else {}
    new_data[field] = truncated
    return LogRecord(raw=record.raw, data=new_data, parse_error=record.parse_error)


def truncate_fields(
    record: LogRecord,
    fields: list[str],
    max_length: int = DEFAULT_MAX_LENGTH,
) -> LogRecord:
    """Return a new LogRecord with each named field truncated."""
    for field in fields:
        record = truncate_field(record, field, max_length)
    return record


def truncate_records(
    records: Iterator[LogRecord],
    fields: list[str],
    max_length: int = DEFAULT_MAX_LENGTH,
) -> Iterator[LogRecord]:
    """Yield records with the specified fields truncated."""
    for record in records:
        yield truncate_fields(record, fields, max_length)
