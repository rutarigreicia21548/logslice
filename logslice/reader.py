"""Stream log lines from files or stdin."""

import io
import sys
from typing import Generator, Iterable, List, Optional
from logslice.parser import LogRecord, parse_line


def stream_lines(sources: List[str]) -> Generator[LogRecord, None, None]:
    """Yield parsed LogRecords from a list of file paths.

    Use "-" to read from stdin.
    """
    for source in sources:
        yield from _read_source(source)


def _read_source(source: str) -> Generator[LogRecord, None, None]:
    if source == "-":
        yield from _iter_lines(sys.stdin, label=None)
    else:
        try:
            with open(source, "r", encoding="utf-8", errors="replace") as fh:
                yield from _iter_lines(fh, label=source)
        except OSError as exc:
            # Emit a synthetic error record so the caller can report it
            raw = f"[logslice] cannot open '{source}': {exc}\n"
            yield LogRecord(raw=raw, data={}, parse_error=str(exc))


def _iter_lines(
    fh: Iterable[str], label: Optional[str]
) -> Generator[LogRecord, None, None]:
    for line in fh:
        record = parse_line(line)
        if label and not record.parse_error:
            # Inject source label if not already present
            if "_source" not in record.data:
                record.data["_source"] = label
        yield record


def stream_records(
    sources: List[str],
    predicate=None,
) -> Generator[LogRecord, None, None]:
    """Stream and optionally filter records from multiple sources."""
    for record in stream_lines(sources):
        if predicate is None or predicate(record):
            yield record
