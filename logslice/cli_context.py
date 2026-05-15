"""CLI helpers for the --before / --after context-window feature."""

import argparse
from typing import Iterable, Iterator

from logslice.parser import LogRecord
from logslice.context import context_window


def add_context_args(parser: argparse.ArgumentParser) -> None:
    """Register -B / -A / -C context flags on *parser*."""
    grp = parser.add_argument_group("context window")
    grp.add_argument(
        "-B",
        "--before",
        metavar="N",
        type=int,
        default=0,
        help="show N records of context before each match (default: 0)",
    )
    grp.add_argument(
        "-A",
        "--after",
        metavar="N",
        type=int,
        default=0,
        help="show N records of context after each match (default: 0)",
    )
    grp.add_argument(
        "-C",
        "--context",
        metavar="N",
        type=int,
        default=None,
        help="show N records of context before AND after each match",
    )


def apply_context(
    records: Iterable[LogRecord],
    args: argparse.Namespace,
    predicate,
) -> Iterator[LogRecord]:
    """Wrap *records* with a context window if any context flags are set.

    *predicate* is the same filter already applied to the pipeline; we need
    it again so context_window can identify which records are "matches".
    """
    before = args.before
    after = args.after
    if args.context is not None:
        before = args.context
        after = args.context

    if before == 0 and after == 0:
        # No context requested — pass through unchanged.
        return iter(records)

    return context_window(records, predicate, before=before, after=after)
