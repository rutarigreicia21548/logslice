"""Field value masking with pattern-based redaction."""

import re
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogRecord, get


_BUILTIN_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "token": re.compile(r"\b[A-Za-z0-9_\-]{20,}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
}


def _get_pattern(pattern: str) -> re.Pattern:
    """Return a compiled regex, resolving built-in names."""
    if pattern in _BUILTIN_PATTERNS:
        return _BUILTIN_PATTERNS[pattern]
    return re.compile(pattern)


def mask_value(value: str, pattern: str, replacement: str = "***") -> str:
    """Replace all matches of *pattern* in *value* with *replacement*."""
    if not isinstance(value, str):
        return value
    compiled = _get_pattern(pattern)
    return compiled.sub(replacement, value)


def mask_field(
    record: LogRecord,
    field: str,
    pattern: str,
    replacement: str = "***",
) -> LogRecord:
    """Return a new LogRecord with *field* masked using *pattern*."""
    value = get(record, field)
    if value is None:
        return record
    masked = mask_value(str(value), pattern, replacement)
    updated = dict(record.data)
    updated[field] = masked
    return LogRecord(raw=record.raw, data=updated, parse_error=record.parse_error)


def mask_records(
    records: Iterable[LogRecord],
    fields: List[str],
    pattern: str,
    replacement: str = "***",
) -> Iterator[LogRecord]:
    """Yield records with each field in *fields* masked."""
    for record in records:
        for field in fields:
            record = mask_field(record, field, pattern, replacement)
        yield record
