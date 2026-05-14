"""Aggregation utilities for counting and summarizing log records."""

from collections import Counter, defaultdict
from typing import Iterable, Dict, Any

from logslice.parser import LogRecord, get


def count_by_field(records: Iterable[LogRecord], field: str) -> Counter:
    """Count log records grouped by the value of a given field."""
    counter: Counter = Counter()
    for record in records:
        value = get(record, field)
        key = str(value) if value is not None else "<missing>"
        counter[key] += 1
    return counter


def count_by_level(records: Iterable[LogRecord]) -> Counter:
    """Convenience wrapper: count records grouped by log level."""
    return count_by_field(records, "level")


def count_by_service(records: Iterable[LogRecord]) -> Counter:
    """Convenience wrapper: count records grouped by service."""
    return count_by_field(records, "service")


def summarize(records: Iterable[LogRecord]) -> Dict[str, Any]:
    """Return a summary dict with totals broken down by level and service."""
    total = 0
    by_level: Counter = Counter()
    by_service: Counter = Counter()

    for record in records:
        total += 1
        level = get(record, "level")
        service = get(record, "service")
        by_level[str(level) if level is not None else "<missing>"] += 1
        by_service[str(service) if service is not None else "<missing>"] += 1

    return {
        "total": total,
        "by_level": dict(by_level),
        "by_service": dict(by_service),
    }


def group_by_field(records: Iterable[LogRecord], field: str) -> Dict[str, list]:
    """Group log records into lists keyed by the value of a given field."""
    groups: Dict[str, list] = defaultdict(list)
    for record in records:
        value = get(record, field)
        key = str(value) if value is not None else "<missing>"
        groups[key].append(record)
    return dict(groups)
