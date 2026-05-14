"""CLI helpers for field transformation arguments."""

import argparse
from typing import Callable, List
from logslice.parser import LogRecord
from logslice.transform import rename_field, add_field, drop_field, transform_records


def add_transform_args(parser: argparse.ArgumentParser) -> None:
    """Register --rename, --add-field, and --drop-field options."""
    parser.add_argument(
        "--rename",
        metavar="SRC:DST",
        action="append",
        default=[],
        help="Rename a field: --rename old:new",
    )
    parser.add_argument(
        "--add-field",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Add or overwrite a field: --add-field env=prod",
    )
    parser.add_argument(
        "--drop-field",
        metavar="FIELD",
        action="append",
        default=[],
        help="Remove a field from every record: --drop-field secret",
    )


def _parse_rename(spec: str):
    """Parse 'src:dst' into (src, dst). Raises ValueError on bad format."""
    parts = spec.split(":", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid --rename spec: {spec!r}. Expected SRC:DST")
    return parts[0], parts[1]


def _parse_add_field(spec: str):
    """Parse 'key=value' into (key, value). Raises ValueError on bad format."""
    parts = spec.split("=", 1)
    if len(parts) != 2 or not parts[0]:
        raise ValueError(f"Invalid --add-field spec: {spec!r}. Expected KEY=VALUE")
    return parts[0], parts[1]


def apply_transforms(args: argparse.Namespace, records):
    """Build and apply all requested transforms from parsed CLI args."""
    fns: List[Callable[[LogRecord], LogRecord]] = []

    for spec in args.rename:
        src, dst = _parse_rename(spec)
        fns.append(lambda r, s=src, d=dst: rename_field(r, s, d))

    for spec in args.add_field:
        key, value = _parse_add_field(spec)
        fns.append(lambda r, k=key, v=value: add_field(r, k, v))

    for field in args.drop_field:
        fns.append(lambda r, f=field: drop_field(r, f))

    if not fns:
        return records
    return transform_records(records, fns)
