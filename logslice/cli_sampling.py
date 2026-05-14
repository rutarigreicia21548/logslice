"""CLI helpers for the --sample and --every-nth options."""

from __future__ import annotations

import argparse
from typing import Iterable, Iterator

from logslice.parser import LogRecord
from logslice.sampling import every_nth, sample_records


def add_sampling_args(parser: argparse.ArgumentParser) -> None:
    """Register sampling-related arguments on *parser*."""
    group = parser.add_argument_group("sampling")
    group.add_argument(
        "--sample",
        metavar="RATE",
        type=float,
        default=None,
        help="Keep only a random fraction of records (0.0–1.0).",
    )
    group.add_argument(
        "--sample-field",
        metavar="FIELD",
        default=None,
        dest="sample_field",
        help="Key sampling on this field so related records stay together.",
    )
    group.add_argument(
        "--every-nth",
        metavar="N",
        type=int,
        default=None,
        dest="every_nth",
        help="Keep every N-th record (deterministic, position-based).",
    )


def apply_sampling(
    records: Iterable[LogRecord],
    args: argparse.Namespace,
) -> Iterator[LogRecord]:
    """Apply sampling filters described by *args* to *records*.

    The --sample and --every-nth options are mutually exclusive; if both are
    supplied, --sample takes precedence and --every-nth is ignored.

    Args:
        records: Source iterable of parsed log records.
        args:    Parsed CLI namespace (expects ``sample``, ``sample_field``,
                 and ``every_nth`` attributes).

    Yields:
        Records after the requested sampling has been applied.
    """
    rate: float | None = getattr(args, "sample", None)
    field: str | None = getattr(args, "sample_field", None)
    nth: int | None = getattr(args, "every_nth", None)

    if rate is not None:
        yield from sample_records(records, rate=rate, field=field)
    elif nth is not None:
        yield from every_nth(records, n=nth)
    else:
        yield from records
