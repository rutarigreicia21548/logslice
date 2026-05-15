"""CLI helpers for the --split-by feature."""

from __future__ import annotations

import argparse
from typing import Iterator

from logslice.parser import LogRecord
from logslice.split import split_records


def add_split_args(parser: argparse.ArgumentParser) -> None:
    """Register split-related arguments on *parser*."""
    parser.add_argument(
        "--split-by",
        metavar="FIELD",
        default=None,
        help="Split output into separate files by the value of FIELD.",
    )
    parser.add_argument(
        "--split-dir",
        metavar="DIR",
        default="split_output",
        help="Directory to write split files into (default: split_output).",
    )
    parser.add_argument(
        "--split-placeholder",
        metavar="LABEL",
        default="_unknown",
        help="Bucket label for records missing the split field (default: _unknown).",
    )


def apply_split(
    records: Iterator[LogRecord],
    args: argparse.Namespace,
) -> Iterator[LogRecord]:
    """If --split-by is set, tee records to per-bucket files and pass them through.

    Records are still yielded so the normal output pipeline is unaffected.
    """
    if not getattr(args, "split_by", None):
        yield from records
        return

    import os
    from logslice.split import make_output_path

    field = args.split_by
    directory = args.split_dir
    placeholder = args.split_placeholder
    os.makedirs(directory, exist_ok=True)
    handles: dict = {}
    try:
        for key, record in split_records(records, field, placeholder):
            if key not in handles:
                path = make_output_path(directory, key, ".log")
                handles[key] = open(path, "a", encoding="utf-8")  # noqa: WPS515
            handles[key].write(record.raw + "\n")
            yield record
    finally:
        for fh in handles.values():
            fh.close()
