"""CLI helpers for the --timeline feature."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Iterable, Iterator

from logslice.parser import LogRecord
from logslice.timeline import iter_timeline


def add_timeline_args(parser: argparse.ArgumentParser) -> None:
    """Register timeline-related arguments on *parser*."""
    group = parser.add_argument_group("timeline")
    group.add_argument(
        "--timeline",
        action="store_true",
        default=False,
        help="Print a per-bucket summary instead of individual records.",
    )
    group.add_argument(
        "--timeline-interval",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Bucket width in seconds (default: 60).",
    )


def _fmt_ts(ts: float) -> str:
    """Format an epoch float as a UTC datetime string."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def apply_timeline(
    args: argparse.Namespace,
    records: Iterable[LogRecord],
) -> Iterator[LogRecord]:
    """If --timeline is set, print a summary and yield nothing; otherwise pass records through."""
    if not getattr(args, "timeline", False):
        yield from records
        return

    interval = getattr(args, "timeline_interval", 60.0)
    for bucket_ts, bucket_records in iter_timeline(records, interval=interval):
        label = _fmt_ts(bucket_ts)
        print(f"{label}  {len(bucket_records):>6} records", file=sys.stdout)
    # generator exhausted; yield nothing so the normal output path is skipped
