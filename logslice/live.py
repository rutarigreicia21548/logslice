"""Live mode entry point: wire watcher → filter → formatter → output."""

from __future__ import annotations

import sys
from typing import TextIO

from logslice.watcher import watch_records, Predicate
from logslice.formatter import format_record
from logslice.output import detect_color


def run_live(
    paths: list[str],
    *,
    follow_stdin: bool = False,
    predicate: Predicate | None = None,
    fmt: str = "pretty",
    color: bool | None = None,
    out: TextIO = sys.stdout,
    poll_interval: float = 0.1,
) -> None:
    """Tail *paths* (and optionally stdin), printing matching records.

    Args:
        paths: Log file paths to follow.
        follow_stdin: Whether to also tail stdin.
        predicate: Optional combined filter predicate.
        fmt: Output format — ``"pretty"`` or ``"json"``.
        color: Force color on/off; ``None`` means auto-detect.
        out: Output stream (defaults to stdout).
        poll_interval: File poll cadence in seconds.
    """
    use_color = detect_color(out) if color is None else color

    try:
        for record in watch_records(
            paths,
            follow_stdin=follow_stdin,
            predicate=predicate,
            poll_interval=poll_interval,
        ):
            line = format_record(record, fmt=fmt, color=use_color)
            out.write(line + "\n")
            out.flush()
    except KeyboardInterrupt:
        # Graceful exit on Ctrl-C — standard tail behaviour
        pass
