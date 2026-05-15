"""Flatten nested JSON log records into dot-notation keys."""

from typing import Any, Dict, Iterator
from logslice.parser import LogRecord


def flatten_dict(data: Dict[str, Any], prefix: str = "", sep: str = ".") -> Dict[str, Any]:
    """Recursively flatten a nested dictionary using dot-notation keys."""
    result: Dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key
        if isinstance(value, dict):
            nested = flatten_dict(value, prefix=full_key, sep=sep)
            result.update(nested)
        else:
            result[full_key] = value
    return result


def flatten_record(record: LogRecord, sep: str = ".") -> LogRecord:
    """Return a new LogRecord with all nested fields flattened.

    The raw line is preserved unchanged. Only the parsed data is flattened.
    If the record has a parse error, it is returned as-is.
    """
    if record.get("_parse_error") or not record.data:
        return record

    flat_data = flatten_dict(record.data, sep=sep)
    return LogRecord(raw=record.raw, data=flat_data)


def flatten_records(
    records: Iterator[LogRecord], sep: str = "."
) -> Iterator[LogRecord]:
    """Yield flattened versions of each record in the stream."""
    for record in records:
        yield flatten_record(record, sep=sep)
