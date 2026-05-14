"""CLI helpers for field redaction arguments."""

import argparse
from typing import Iterable, Iterator
from logslice.parser import LogRecord
from logslice.redact import redact_records


def add_redact_args(parser: argparse.ArgumentParser) -> None:
    """Register --redact argument on an existing argument parser."""
    parser.add_argument(
        "--redact",
        metavar="FIELD",
        action="append",
        default=[],
        dest="redact_fields",
        help="Redact the value of FIELD in output (repeatable).",
    )


def apply_redaction(
    records: Iterable[LogRecord], args: argparse.Namespace
) -> Iterator[LogRecord]:
    """Apply redaction to a record stream based on parsed CLI arguments."""
    fields: list[str] = getattr(args, "redact_fields", []) or []
    return redact_records(records, fields)
