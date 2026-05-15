"""Group log records into time buckets for timeline analysis."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Iterator, List, Tuple

from logslice.parser import LogRecord
from logslice.timefilter import extract_timestamp


def _bucket_key(ts: float, interval: float) -> float:
    """Return the start of the bucket containing *ts*."""
    return float(int(ts // interval) * interval)


def bucket_records(
    records: Iterable[LogRecord],
    interval: float = 60.0,
) -> Dict[float, List[LogRecord]]:
    """Group *records* into fixed-width time buckets of *interval* seconds.

    Records whose timestamp cannot be extracted are silently skipped.
    Returns an ordered dict mapping bucket-start (epoch float) -> list of records.
    """
    buckets: Dict[float, List[LogRecord]] = defaultdict(list)
    for record in records:
        ts = extract_timestamp(record)
        if ts is None:
            continue
        key = _bucket_key(ts, interval)
        buckets[key].append(record)
    return dict(sorted(buckets.items()))


def timeline_counts(
    records: Iterable[LogRecord],
    interval: float = 60.0,
) -> List[Tuple[float, int]]:
    """Return a sorted list of (bucket_start, count) pairs."""
    buckets = bucket_records(records, interval)
    return [(ts, len(recs)) for ts, recs in sorted(buckets.items())]


def iter_timeline(
    records: Iterable[LogRecord],
    interval: float = 60.0,
) -> Iterator[Tuple[float, List[LogRecord]]]:
    """Yield (bucket_start, records) tuples in chronological order."""
    buckets = bucket_records(records, interval)
    for ts in sorted(buckets):
        yield ts, buckets[ts]
