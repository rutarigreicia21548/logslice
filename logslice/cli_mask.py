"""CLI integration for field masking."""

import argparse
from typing import Iterator

from logslice.parser import LogRecord
from logslice.mask import mask_records


def add_mask_args(parser: argparse.ArgumentParser) -> None:
    """Register --mask-field and --mask-pattern flags on *parser*."""
    parser.add_argument(
        "--mask-field",
        dest="mask_fields",
        metavar="FIELD",
        action="append",
        default=[],
        help="Field whose value should be masked (repeatable).",
    )
    parser.add_argument(
        "--mask-pattern",
        dest="mask_pattern",
        metavar="PATTERN",
        default=None,
        help=(
            "Regex pattern or built-in name (email, ipv4, token, credit_card) "
            "to match within field values."
        ),
    )
    parser.add_argument(
        "--mask-replacement",
        dest="mask_replacement",
        metavar="TEXT",
        default="***",
        help="Replacement string for masked values (default: ***).",
    )


def apply_masking(
    records: Iterator[LogRecord],
    args: argparse.Namespace,
) -> Iterator[LogRecord]:
    """Apply masking to *records* based on parsed CLI *args*."""
    fields = getattr(args, "mask_fields", []) or []
    pattern = getattr(args, "mask_pattern", None)
    replacement = getattr(args, "mask_replacement", "***") or "***"

    if not fields or not pattern:
        return records

    return mask_records(records, fields, pattern, replacement)
