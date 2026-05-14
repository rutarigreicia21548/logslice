"""Deduplication of log records based on a fingerprint field or message content."""

from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, Iterator, Optional

from logslice.parser import LogRecord, get


def _fingerprint(record: LogRecord, field: Optional[str] = None) -> str:
    """Return a string fingerprint for a log record.

    If *field* is given, use the value of that field; otherwise fall back to
    the raw line so that even non-JSON lines can be deduplicated.
    """
    if field is not None:
        value = get(record, field)
        if value is not None:
            return str(value)
    # Default: use the raw line (stripped) as the fingerprint.
    return record.raw.strip()


def dedup_records(
    records: Iterable[LogRecord],
    *,
    field: Optional[str] = None,
    window: int = 256,
) -> Iterator[LogRecord]:
    """Yield records, skipping duplicates seen within the last *window* entries.

    Parameters
    ----------
    records:
        Source iterable of :class:`~logslice.parser.LogRecord` objects.
    field:
        Optional field name to use as the deduplication key.  When *None*
        the raw log line is used.
    window:
        Maximum number of recent fingerprints to remember.  Older entries are
        evicted in insertion order (LRU-style) to bound memory usage.
    """
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window!r}")

    seen: OrderedDict[str, None] = OrderedDict()

    for record in records:
        fp = _fingerprint(record, field)
        if fp in seen:
            # Move to end to refresh recency, then skip.
            seen.move_to_end(fp)
            continue

        seen[fp] = None
        if len(seen) > window:
            seen.popitem(last=False)

        yield record
