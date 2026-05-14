"""Write formatted log records to an output stream."""

from __future__ import annotations

import os
import sys
from typing import Iterable, TextIO

from logslice.parser import LogRecord
from logslice.formatter import format_record


def detect_color(stream: TextIO = sys.stdout) -> bool:
    """Return True when color output is appropriate for *stream*.

    Color is disabled when:
    - the stream is not a TTY, or
    - the ``NO_COLOR`` environment variable is set, or
    - the ``TERM`` environment variable is ``'dumb'``.
    """
    if not hasattr(stream, "isatty") or not stream.isatty():
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True


def write_records(
    records: Iterable[LogRecord],
    fmt: str = "pretty",
    color: bool | None = None,
    stream: TextIO = sys.stdout,
) -> int:
    """Write each record in *records* to *stream*, returning the count written.

    If *color* is ``None`` the value is auto-detected from the stream.
    """
    if color is None:
        color = detect_color(stream)

    count = 0
    for record in records:
        line = format_record(record, fmt=fmt, color=color)
        stream.write(line + "\n")
        count += 1
    return count
