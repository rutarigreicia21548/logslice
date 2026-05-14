"""High-level watcher: tail sources and emit parsed, filtered LogRecords."""

from typing import Iterator, Callable

from logslice.parser import LogRecord, parse_line
from logslice.tail import tail_sources


Predicate = Callable[[LogRecord], bool]


def watch_records(
    paths: list[str],
    *,
    follow_stdin: bool = False,
    predicate: Predicate | None = None,
    poll_interval: float = 0.1,
) -> Iterator[LogRecord]:
    """Stream LogRecords from tailed files/stdin, applying an optional filter.

    Each record is annotated with a ``source`` field matching the file path
    (or ``<stdin>``) unless the log line already contains a ``source`` key.

    Args:
        paths: File paths to tail.
        follow_stdin: Also read from stdin.
        predicate: Optional filter; only matching records are yielded.
        poll_interval: Seconds between file polls.

    Yields:
        Parsed and optionally filtered :class:`~logslice.parser.LogRecord`.
    """
    for source, raw_line in tail_sources(
        paths, follow_stdin=follow_stdin, poll_interval=poll_interval
    ):
        record = parse_line(raw_line)
        # Inject source label if not already present
        if record.data is not None and "source" not in record.data:
            record.data["source"] = source

        if predicate is None or predicate(record):
            yield record
