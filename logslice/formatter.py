"""Output formatting for log records."""

import json
from typing import Optional
from logslice.parser import LogRecord, get

ANSI_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "WARN": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[35m",
    "FATAL": "\033[35m",
}
ANSI_RESET = "\033[0m"
ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"


def format_pretty(record: LogRecord, color: bool = True) -> str:
    """Format a log record as a human-readable line."""
    if record.parse_error:
        prefix = f"{ANSI_DIM}[raw]{ANSI_RESET} " if color else "[raw] "
        return prefix + record.raw.rstrip()

    timestamp = get(record, "timestamp") or get(record, "time") or get(record, "ts") or ""
    level = (get(record, "level") or get(record, "severity") or "").upper()
    service = get(record, "service") or get(record, "app") or ""
    message = get(record, "message") or get(record, "msg") or ""

    level_color = ANSI_COLORS.get(level, "") if color else ""
    reset = ANSI_RESET if color else ""
    bold = ANSI_BOLD if color else ""
    dim = ANSI_DIM if color else ""

    parts = []
    if timestamp:
        parts.append(f"{dim}{timestamp}{reset}")
    if service:
        parts.append(f"{bold}[{service}]{reset}")
    if level:
        parts.append(f"{level_color}{level}{reset}")
    if message:
        parts.append(message)

    return " ".join(parts) if parts else record.raw.rstrip()


def format_json(record: LogRecord) -> str:
    """Format a log record as compact JSON (passthrough for valid records)."""
    if record.parse_error:
        return record.raw.rstrip()
    return json.dumps(record.data, separators=(",", ":"))


def format_record(record: LogRecord, fmt: str = "pretty", color: bool = True) -> str:
    """Dispatch to the appropriate formatter."""
    if fmt == "json":
        return format_json(record)
    return format_pretty(record, color=color)
