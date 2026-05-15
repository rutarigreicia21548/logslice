"""CLI integration for the flatten feature."""

import argparse
from typing import Iterator

from logslice.parser import LogRecord
from logslice.flatten import flatten_records


def add_flatten_args(parser: argparse.ArgumentParser) -> None:
    """Register --flatten and --flatten-sep arguments on the given parser."""
    parser.add_argument(
        "--flatten",
        action="store_true",
        default=False,
        help="Flatten nested JSON fields into dot-notation keys (e.g. a.b.c).",
    )
    parser.add_argument(
        "--flatten-sep",
        metavar="SEP",
        default=".",
        help="Separator to use when flattening nested keys (default: '.').",
    )


def apply_flatten(
    records: Iterator[LogRecord], args: argparse.Namespace
) -> Iterator[LogRecord]:
    """Apply flattening to the record stream if --flatten is set."""
    if not getattr(args, "flatten", False):
        return records
    sep = getattr(args, "flatten_sep", ".")
    return flatten_records(records, sep=sep)
