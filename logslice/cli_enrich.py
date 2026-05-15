"""CLI argument handling for field enrichment."""

import argparse
from typing import Dict
from logslice.enrich import enrich_records
from logslice.parser import LogRecord


def add_enrich_args(parser: argparse.ArgumentParser) -> None:
    """Register --enrich flags on an argument parser."""
    parser.add_argument(
        "--enrich",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help=(
            "Add a static field to every record (if not already present). "
            "Can be repeated. Example: --enrich env=production"
        ),
    )


def _parse_enrich_arg(arg: str) -> tuple:
    """Parse a KEY=VALUE string into a (key, value) tuple."""
    if "=" not in arg:
        raise argparse.ArgumentTypeError(
            f"Invalid --enrich argument {arg!r}: expected KEY=VALUE"
        )
    key, _, value = arg.partition("=")
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError(
            f"Invalid --enrich argument {arg!r}: key must not be empty"
        )
    return key, value


def apply_enrichment(records, args: argparse.Namespace):
    """Apply static enrichment fields from parsed CLI args to the record stream."""
    raw_enrichments = getattr(args, "enrich", []) or []
    if not raw_enrichments:
        yield from records
        return

    static_fields: Dict[str, str] = {}
    for arg in raw_enrichments:
        key, value = _parse_enrich_arg(arg)
        static_fields[key] = value

    yield from enrich_records(records, static_fields=static_fields)
