"""CLI helpers for truncation arguments."""

import argparse
from typing import Iterator

from logslice.parser import LogRecord
from logslice.truncate import truncate_records, DEFAULT_MAX_LENGTH


def add_truncate_args(parser: argparse.ArgumentParser) -> None:
    """Register --truncate-field and --max-length arguments on parser."""
    parser.add_argument(
        "--truncate-field",
        dest="truncate_fields",
        metavar="FIELD",
        action="append",
        default=[],
        help="Truncate the value of FIELD to --max-length characters (repeatable).",
    )
    parser.add_argument(
        "--max-length",
        dest="max_length",
        type=int,
        default=DEFAULT_MAX_LENGTH,
        metavar="N",
        help=f"Maximum field value length before truncation (default: {DEFAULT_MAX_LENGTH}).",
    )


def apply_truncation(
    records: Iterator[LogRecord],
    args: argparse.Namespace,
) -> Iterator[LogRecord]:
    """Apply truncation from parsed CLI args, or pass records through unchanged."""
    fields = getattr(args, "truncate_fields", []) or []
    max_length = getattr(args, "max_length", DEFAULT_MAX_LENGTH)
    if not fields:
        return records
    return truncate_records(records, fields, max_length)
