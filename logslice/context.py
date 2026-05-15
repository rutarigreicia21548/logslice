"""Context window extraction: yield records surrounding a matching record."""

from collections import deque
from typing import Callable, Iterable, Iterator

from logslice.parser import LogRecord


def context_window(
    records: Iterable[LogRecord],
    predicate: Callable[[LogRecord], bool],
    before: int = 0,
    after: int = 0,
) -> Iterator[LogRecord]:
    """Yield records that match *predicate* plus up to *before* records before
    and *after* records after each match.  Overlapping windows are merged so
    no record is emitted more than once."""
    if before < 0:
        raise ValueError("before must be >= 0")
    if after < 0:
        raise ValueError("after must be >= 0")

    buf: deque[LogRecord] = deque(maxlen=before + 1)
    # countdown: how many more post-match records to emit
    emit_countdown = 0
    # track which records have already been yielded by index
    emitted_up_to = -1
    pending: list[LogRecord] = []

    def _flush_pending(up_to_index: int) -> Iterator[LogRecord]:
        nonlocal emitted_up_to
        while pending and pending[0][0] <= up_to_index:
            idx, rec = pending.pop(0)
            if idx > emitted_up_to:
                emitted_up_to = idx
                yield rec

    # We need stable indices; materialise lazily with an enumeration.
    indexed = enumerate(records)

    buf_list: list[tuple[int, LogRecord]] = []

    for idx, record in indexed:
        buf_list.append((idx, record))
        # Keep only the last (before+1) items
        if len(buf_list) > before + 1:
            buf_list.pop(0)

        if emit_countdown > 0:
            if idx > emitted_up_to:
                emitted_up_to = idx
                emit_countdown -= 1
                yield record
            else:
                emit_countdown -= 1
            continue

        if predicate(record):
            # Emit buffered pre-context
            for b_idx, b_rec in buf_list:
                if b_idx > emitted_up_to:
                    emitted_up_to = b_idx
                    yield b_rec
            emit_countdown = after
