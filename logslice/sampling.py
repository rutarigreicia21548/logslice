"""Sampling utilities for reducing log volume."""

from __future__ import annotations

import hashlib
from typing import Iterable, Iterator

from logslice.parser import LogRecord, get


def _hash_record(record: LogRecord, field: str | None) -> int:
    """Return a stable integer hash for a record, optionally keyed by a field."""
    if field is not None:
        value = str(get(record, field, record.raw))
    else:
        value = record.raw
    digest = hashlib.md5(value.encode(), usedforsecurity=False).hexdigest()
    return int(digest, 16)


def sample_records(
    records: Iterable[LogRecord],
    rate: float,
    field: str | None = None,
) -> Iterator[LogRecord]:
    """Yield a deterministic subset of *records* at the given *rate*.

    Args:
        records: Source iterable of parsed log records.
        rate: Fraction of records to keep, between 0.0 and 1.0 inclusive.
        field: When provided, sampling is keyed on this field value so that
               all records sharing the same value are kept or dropped together.

    Yields:
        Records whose hash falls within the kept fraction.
    """
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"rate must be between 0.0 and 1.0, got {rate!r}")

    if rate == 1.0:
        yield from records
        return

    if rate == 0.0:
        return

    # Use 2**128 as the modulus for MD5 hashes.
    threshold = int(rate * (2 ** 128))

    for record in records:
        if _hash_record(record, field) < threshold:
            yield record


def every_nth(
    records: Iterable[LogRecord],
    n: int,
) -> Iterator[LogRecord]:
    """Yield every *n*-th record from *records* (1-based).

    Args:
        records: Source iterable of parsed log records.
        n: Step size; must be a positive integer.

    Yields:
        Every n-th record.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n!r}")

    for i, record in enumerate(records, start=1):
        if i % n == 0:
            yield record
