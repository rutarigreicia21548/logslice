"""Output writing utilities for logslice."""

import sys
from typing import Iterable, Optional, TextIO
from logslice.parser import LogRecord
from logslice.formatter import format_record


def write_records(
    records: Iterable[LogRecord],
    fmt: str = "pretty",
    color: bool = True,
    out: Optional[TextIO] = None,
    err: Optional[TextIO] = None,
    max_records: Optional[int] = None,
) -> int:
    """Write formatted log records to *out* (default stdout).

    Returns the total number of records written.
    """
    if out is None:
        out = sys.stdout
    if err is None:
        err = sys.stderr

    count = 0
    try:
        for record in records:
            if max_records is not None and count >= max_records:
                break
            line = format_record(record, fmt=fmt, color=color)
            out.write(line + "\n")
            count += 1
    except BrokenPipeError:
        # Consumer closed the pipe (e.g. piped to `head`)
        pass
    except KeyboardInterrupt:
        pass
    return count


def detect_color(out: Optional[TextIO] = None) -> bool:
    """Return True if the output stream supports ANSI color."""
    stream = out or sys.stdout
    return hasattr(stream, "isatty") and stream.isatty()
