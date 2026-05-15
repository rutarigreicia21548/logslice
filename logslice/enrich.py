"""Field enrichment: add derived or static fields to log records."""

from typing import Callable, Dict, Iterable, Optional
from logslice.parser import LogRecord


def enrich_with_static(
    record: LogRecord, key: str, value: str
) -> LogRecord:
    """Return a new record with a static field added (does not overwrite)."""
    if key in record.data:
        return record
    new_data = dict(record.data)
    new_data[key] = value
    return LogRecord(data=new_data, raw=record.raw, parse_error=record.parse_error)


def enrich_with_computed(
    record: LogRecord, key: str, fn: Callable[[LogRecord], Optional[str]]
) -> LogRecord:
    """Return a new record with a computed field. fn receives the record."""
    value = fn(record)
    if value is None:
        return record
    new_data = dict(record.data)
    new_data[key] = value
    return LogRecord(data=new_data, raw=record.raw, parse_error=record.parse_error)


def enrich_records(
    records: Iterable[LogRecord],
    static_fields: Optional[Dict[str, str]] = None,
    computed_fields: Optional[Dict[str, Callable[[LogRecord], Optional[str]]]] = None,
) -> Iterable[LogRecord]:
    """Apply static and computed enrichments to each record in the stream."""
    static_fields = static_fields or {}
    computed_fields = computed_fields or {}

    for record in records:
        for key, value in static_fields.items():
            record = enrich_with_static(record, key, value)
        for key, fn in computed_fields.items():
            record = enrich_with_computed(record, key, fn)
        yield record
