"""Throttle log records by suppressing repeated identical messages within a time window."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Iterable, Iterator, Optional

from logslice.parser import LogRecord, get


def _message_key(record: LogRecord, field: str) -> str:
    """Return the value used to identify duplicate records."""
    value = get(record, field)
    if value is None:
        return record.raw
    return str(value)


def throttle_records(
    records: Iterable[LogRecord],
    window: float,
    field: str = "message",
    max_per_window: int = 1,
) -> Iterator[LogRecord]:
    """Suppress records whose key appears more than *max_per_window* times within *window* seconds.

    Args:
        records: Source log records.
        window: Rolling time window in seconds.
        field: Field used to identify duplicate records.
        max_per_window: Maximum number of times a key is emitted per window.

    Yields:
        Records that have not been throttled.
    """
    counts: dict[str, list[float]] = defaultdict(list)

    for record in records:
        key = _message_key(record, field)
        now = time.monotonic()
        timestamps = counts[key]
        # Evict timestamps outside the current window
        counts[key] = [t for t in timestamps if now - t < window]
        if len(counts[key]) < max_per_window:
            counts[key].append(now)
            yield record


def make_throttle_filter(
    window: float,
    field: str = "message",
    max_per_window: int = 1,
):
    """Return a callable that wraps an iterable with throttle_records."""
    def apply(records: Iterable[LogRecord]) -> Iterator[LogRecord]:
        return throttle_records(records, window=window, field=field, max_per_window=max_per_window)
    return apply
