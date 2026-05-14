"""Format LogRecord objects for terminal or JSON output."""

from __future__ import annotations

import json
from typing import Optional

from logslice.parser import LogRecord, get
from logslice.highlight import highlight_level, highlight_field, colorize

_KNOWN_FIELDS = {"timestamp", "time", "ts", "level", "severity", "msg", "message", "service"}


def format_pretty(record: LogRecord, color: bool = True) -> str:
    """Return a human-readable single-line representation of *record*."""
    parts: list[str] = []

    ts = get(record, "timestamp") or get(record, "time") or get(record, "ts")
    if ts:
        parts.append(colorize(str(ts), "dim", enabled=color))

    level = get(record, "level") or get(record, "severity") or ""
    if level:
        parts.append(highlight_level(str(level), enabled=color))

    service = get(record, "service")
    if service:
        parts.append(colorize(f"[{service}]", "cyan", enabled=color))

    msg = get(record, "msg") or get(record, "message") or ""
    if msg:
        parts.append(colorize(str(msg), "bold", enabled=color))

    if record.data:
        extras = [
            highlight_field(k, str(v), enabled=color)
            for k, v in record.data.items()
            if k not in _KNOWN_FIELDS
        ]
        parts.extend(extras)

    return " ".join(parts)


def format_json(record: LogRecord) -> str:
    """Return the compact JSON representation of *record*."""
    if record.data is not None:
        return json.dumps(record.data, separators=(",", ":"))
    return record.raw.rstrip("\n")


def format_record(
    record: LogRecord,
    fmt: str = "pretty",
    color: bool = True,
) -> str:
    """Dispatch to the appropriate formatter.

    *fmt* may be ``'pretty'`` or ``'json'``.
    """
    if fmt == "json":
        return format_json(record)
    return format_pretty(record, color=color)
