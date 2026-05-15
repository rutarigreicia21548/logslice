"""Rate limiting for log record streams."""

import time
from typing import Iterable, Iterator
from logslice.parser import LogRecord


def rate_limit_records(
    records: Iterable[LogRecord],
    max_per_second: float,
) -> Iterator[LogRecord]:
    """Yield records, sleeping as needed to enforce a maximum throughput rate.

    Args:
        records: Source iterable of log records.
        max_per_second: Maximum number of records to emit per second.
            Must be a positive number.

    Yields:
        LogRecord instances at the requested rate.

    Raises:
        ValueError: If max_per_second is not positive.
    """
    if max_per_second <= 0:
        raise ValueError(f"max_per_second must be positive, got {max_per_second}")

    interval = 1.0 / max_per_second
    last = None

    for record in records:
        now = time.monotonic()
        if last is not None:
            elapsed = now - last
            wait = interval - elapsed
            if wait > 0:
                time.sleep(wait)
        last = time.monotonic()
        yield record


def burst_limit_records(
    records: Iterable[LogRecord],
    burst_size: int,
    window_seconds: float = 1.0,
) -> Iterator[LogRecord]:
    """Yield up to burst_size records per window, dropping the rest.

    Args:
        records: Source iterable of log records.
        burst_size: Maximum records allowed per window.
        window_seconds: Duration of each time window in seconds.

    Yields:
        LogRecord instances that fall within the burst budget.

    Raises:
        ValueError: If burst_size or window_seconds is not positive.
    """
    if burst_size <= 0:
        raise ValueError(f"burst_size must be positive, got {burst_size}")
    if window_seconds <= 0:
        raise ValueError(f"window_seconds must be positive, got {window_seconds}")

    window_start = time.monotonic()
    count = 0

    for record in records:
        now = time.monotonic()
        if now - window_start >= window_seconds:
            window_start = now
            count = 0
        if count < burst_size:
            count += 1
            yield record
