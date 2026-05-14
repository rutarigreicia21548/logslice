"""Field transformation utilities for log records."""

from typing import Any, Callable, Dict, Iterable, Optional
from logslice.parser import LogRecord


def rename_field(record: LogRecord, src: str, dst: str) -> LogRecord:
    """Return a new record with field `src` renamed to `dst`."""
    if src not in record.data:
        return record
    new_data = dict(record.data)
    new_data[dst] = new_data.pop(src)
    return LogRecord(raw=record.raw, data=new_data, parse_error=record.parse_error)


def add_field(record: LogRecord, key: str, value: Any) -> LogRecord:
    """Return a new record with `key` set to `value` (overwrites if present)."""
    new_data = dict(record.data)
    new_data[key] = value
    return LogRecord(raw=record.raw, data=new_data, parse_error=record.parse_error)


def drop_field(record: LogRecord, key: str) -> LogRecord:
    """Return a new record with `key` removed. No-op if key is absent."""
    if key not in record.data:
        return record
    new_data = {k: v for k, v in record.data.items() if k != key}
    return LogRecord(raw=record.raw, data=new_data, parse_error=record.parse_error)


def apply_transform(
    record: LogRecord,
    fn: Callable[[LogRecord], LogRecord],
) -> LogRecord:
    """Apply an arbitrary transform function to a record."""
    return fn(record)


def transform_records(
    records: Iterable[LogRecord],
    transforms: Iterable[Callable[[LogRecord], LogRecord]],
) -> Iterable[LogRecord]:
    """Apply a sequence of transforms to every record in the stream."""
    fns = list(transforms)
    for record in records:
        for fn in fns:
            record = fn(record)
        yield record
