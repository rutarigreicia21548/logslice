"""CLI integration for the throttle feature."""

from __future__ import annotations

import argparse
from typing import Iterable, Iterator, Optional

from logslice.parser import LogRecord
from logslice.throttle import throttle_records


def add_throttle_args(parser: argparse.ArgumentParser) -> None:
    """Register throttle-related arguments on *parser*."""
    parser.add_argument(
        "--throttle-window",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Suppress duplicate messages seen more than --throttle-max times within SECONDS.",
    )
    parser.add_argument(
        "--throttle-max",
        type=int,
        default=1,
        metavar="N",
        help="Maximum occurrences of a message allowed per throttle window (default: 1).",
    )
    parser.add_argument(
        "--throttle-field",
        type=str,
        default="message",
        metavar="FIELD",
        help="Field used to identify duplicate records (default: message).",
    )


def apply_throttle(
    records: Iterable[LogRecord],
    args: argparse.Namespace,
) -> Iterable[LogRecord]:
    """Apply throttling to *records* if requested via *args*."""
    window: Optional[float] = getattr(args, "throttle_window", None)
    if window is None:
        return records
    max_per_window: int = getattr(args, "throttle_max", 1)
    field: str = getattr(args, "throttle_field", "message")
    return throttle_records(records, window=window, field=field, max_per_window=max_per_window)
