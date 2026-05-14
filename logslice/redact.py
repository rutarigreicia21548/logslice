"""Field redaction for sensitive log data."""

from typing import Iterable, Iterator
from logslice.parser import LogRecord, get

_REDACTED = "[REDACTED]"


def redact_field(record: LogRecord, field: str) -> LogRecord:
    """Return a new LogRecord with the given field value replaced."""
    if record.parsed is None:
        return record
    if field not in record.parsed:
        return record
    new_parsed = dict(record.parsed)
    new_parsed[field] = _REDACTED
    return LogRecord(
        raw=record.raw,
        parsed=new_parsed,
        source=record.source,
        parse_error=record.parse_error,
    )


def redact_fields(record: LogRecord, fields: list[str]) -> LogRecord:
    """Return a new LogRecord with all specified fields redacted."""
    result = record
    for field in fields:
        result = redact_field(result, field)
    return result


def redact_records(
    records: Iterable[LogRecord], fields: list[str]
) -> Iterator[LogRecord]:
    """Yield records with specified fields redacted."""
    if not fields:
        yield from records
        return
    for record in records:
        yield redact_fields(record, fields)
