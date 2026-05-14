"""Filter logic for logslice — apply field-based predicates to LogRecords."""

from typing import Any, Callable, Dict, List, Optional
from logslice.parser import LogRecord, get


FilterPredicate = Callable[[LogRecord], bool]


def make_field_filter(field: str, value: str) -> FilterPredicate:
    """Return a predicate that matches records where field equals value."""

    def predicate(record: LogRecord) -> bool:
        actual = get(record, field)
        if actual is None:
            return False
        return str(actual) == value

    return predicate


def make_level_filter(level: str) -> FilterPredicate:
    """Return a predicate that matches records at or above the given log level."""
    level_order = ["debug", "info", "warning", "warn", "error", "critical"]
    target = level.lower()
    try:
        target_index = level_order.index(target)
    except ValueError:
        # Unknown level — fall back to exact match
        return make_field_filter("level", level)

    def predicate(record: LogRecord) -> bool:
        actual = get(record, "level")
        if actual is None:
            return False
        actual_lower = str(actual).lower()
        # Normalise warn -> warning
        if actual_lower == "warn":
            actual_lower = "warning"
        try:
            return level_order.index(actual_lower) >= target_index
        except ValueError:
            return False

    return predicate


def make_service_filter(service: str) -> FilterPredicate:
    """Return a predicate that matches records from the given service."""
    return make_field_filter("service", service)


def build_filter(predicates: List[FilterPredicate]) -> FilterPredicate:
    """Combine multiple predicates with AND semantics."""
    if not predicates:
        return lambda record: True

    def combined(record: LogRecord) -> bool:
        return all(p(record) for p in predicates)

    return combined


def apply_filter(records: List[LogRecord], predicate: FilterPredicate) -> List[LogRecord]:
    """Return only the records that satisfy the predicate."""
    return [r for r in records if predicate(r)]
