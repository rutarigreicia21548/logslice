"""Multiline log folding: merge continuation lines into a single record."""

from __future__ import annotations

from typing import Iterable, Iterator, Optional

from logslice.parser import LogRecord, parse_line


def is_continuation(line: str, prefix: str) -> bool:
    """Return True if *line* looks like a continuation of the previous record."""
    return line.startswith(prefix)


def fold_multiline(
    lines: Iterable[str],
    continuation_prefix: str = "  ",
    join_with: str = " ",
) -> Iterator[str]:
    """Yield logical lines, merging continuation lines into the preceding one.

    A line that starts with *continuation_prefix* is appended to the
    accumulated buffer rather than emitted as a new record.
    """
    buffer: Optional[str] = None

    for line in lines:
        stripped = line.rstrip("\n")
        if is_continuation(stripped, continuation_prefix):
            if buffer is None:
                # No preceding line — treat as standalone
                buffer = stripped
            else:
                buffer = buffer + join_with + stripped.lstrip()
        else:
            if buffer is not None:
                yield buffer
            buffer = stripped

    if buffer is not None:
        yield buffer


def multiline_records(
    lines: Iterable[str],
    continuation_prefix: str = "  ",
    join_with: str = " ",
) -> Iterator[LogRecord]:
    """Parse records from *lines*, folding multiline entries first."""
    for logical_line in fold_multiline(lines, continuation_prefix, join_with):
        yield parse_line(logical_line)
