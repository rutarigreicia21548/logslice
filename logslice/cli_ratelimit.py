"""CLI integration for rate limiting options."""

import argparse
from typing import Iterable, Iterator
from logslice.parser import LogRecord
from logslice.ratelimit import rate_limit_records, burst_limit_records


def add_ratelimit_args(parser: argparse.ArgumentParser) -> None:
    """Register rate-limiting arguments on an argument parser."""
    group = parser.add_argument_group("rate limiting")
    group.add_argument(
        "--rate-limit",
        metavar="N",
        type=float,
        default=None,
        help="Maximum records to emit per second (e.g. 10.0).",
    )
    group.add_argument(
        "--burst-limit",
        metavar="N",
        type=int,
        default=None,
        help="Maximum records per burst window (see --burst-window).",
    )
    group.add_argument(
        "--burst-window",
        metavar="SECONDS",
        type=float,
        default=1.0,
        help="Burst window size in seconds (default: 1.0).",
    )


def apply_ratelimit(
    records: Iterable[LogRecord],
    args: argparse.Namespace,
) -> Iterator[LogRecord]:
    """Apply rate-limiting pipeline stages based on parsed CLI arguments.

    Args:
        records: Source iterable of log records.
        args: Parsed argument namespace.

    Returns:
        Possibly wrapped iterator respecting the requested limits.
    """
    if args.rate_limit is not None:
        records = rate_limit_records(records, max_per_second=args.rate_limit)
    if args.burst_limit is not None:
        records = burst_limit_records(
            records,
            burst_size=args.burst_limit,
            window_seconds=args.burst_window,
        )
    return records
