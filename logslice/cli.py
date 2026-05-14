"""Command-line interface for logslice."""

import sys
import argparse
from typing import List, Optional

from logslice.parser import parse_line, LogRecord
from logslice.filter import (
    build_filter,
    make_field_filter,
    make_level_filter,
    make_service_filter,
    FilterPredicate,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Stream and filter structured JSON logs from multiple services.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Log files to read. Defaults to stdin if none provided.",
    )
    parser.add_argument(
        "--level", "-l",
        metavar="LEVEL",
        help="Minimum log level to include (e.g. info, warning, error).",
    )
    parser.add_argument(
        "--service", "-s",
        metavar="SERVICE",
        help="Filter to a specific service name.",
    )
    parser.add_argument(
        "--field", "-f",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Filter by arbitrary field. May be repeated.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output the original raw line instead of the parsed JSON.",
    )
    return parser


def parse_field_arg(field_arg: str):
    """Parse a KEY=VALUE string into a (key, value) tuple."""
    if "=" not in field_arg:
        raise argparse.ArgumentTypeError(
            f"--field argument must be in KEY=VALUE format, got: {field_arg!r}"
        )
    key, _, value = field_arg.partition("=")
    return key.strip(), value.strip()


def run(argv: Optional[List[str]] = None) -> int:
    arg_parser = build_arg_parser()
    args = arg_parser.parse_args(argv)

    predicates: List[FilterPredicate] = []
    if args.level:
        predicates.append(make_level_filter(args.level))
    if args.service:
        predicates.append(make_service_filter(args.service))
    for field_arg in args.field:
        try:
            key, value = parse_field_arg(field_arg)
        except argparse.ArgumentTypeError as exc:
            print(f"logslice: {exc}", file=sys.stderr)
            return 2
        predicates.append(make_field_filter(key, value))

    combined = build_filter(predicates)

    sources = [open(f) for f in args.files] if args.files else [sys.stdin]
    try:
        for source in sources:
            for raw_line in source:
                record = parse_line(raw_line)
                if combined(record):
                    if args.raw:
                        print(record["raw"])
                    else:
                        import json
                        data = record.get("data")
                        print(json.dumps(data) if data is not None else record["raw"])
    finally:
        for source in sources:
            if source is not sys.stdin:
                source.close()

    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
