"""Split log records into separate output files by a field value."""

from __future__ import annotations

import os
from typing import Dict, Iterable, Iterator, Optional

from logslice.parser import LogRecord, get


def split_by_field(
    records: Iterable[LogRecord],
    field: str,
    placeholder: str = "_unknown",
) -> Dict[str, list]:
    """Partition records into buckets keyed by the value of *field*.

    Records that lack the field are placed under *placeholder*.
    """
    buckets: Dict[str, list] = {}
    for record in records:
        value = get(record, field)
        key = str(value) if value is not None else placeholder
        buckets.setdefault(key, []).append(record)
    return buckets


def split_records(
    records: Iterable[LogRecord],
    field: str,
    placeholder: str = "_unknown",
) -> Iterator[tuple[str, LogRecord]]:
    """Yield (bucket_key, record) pairs without buffering all records."""
    for record in records:
        value = get(record, field)
        key = str(value) if value is not None else placeholder
        yield key, record


def make_output_path(directory: str, key: str, extension: str = ".log") -> str:
    """Return a safe file path for a bucket *key* inside *directory*."""
    safe_key = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in key)
    return os.path.join(directory, f"{safe_key}{extension}")


def write_split(
    records: Iterable[LogRecord],
    field: str,
    directory: str,
    extension: str = ".log",
    placeholder: str = "_unknown",
) -> Dict[str, int]:
    """Write records split by *field* into files under *directory*.

    Returns a dict mapping each bucket key to the number of records written.
    """
    os.makedirs(directory, exist_ok=True)
    handles: Dict[str, object] = {}
    counts: Dict[str, int] = {}
    try:
        for key, record in split_records(records, field, placeholder):
            if key not in handles:
                path = make_output_path(directory, key, extension)
                handles[key] = open(path, "a", encoding="utf-8")  # noqa: WPS515
                counts[key] = 0
            handles[key].write(record.raw + "\n")  # type: ignore[union-attr]
            counts[key] += 1
    finally:
        for fh in handles.values():
            fh.close()  # type: ignore[union-attr]
    return counts
