"""Live tail support: follow log files and stdin for new lines."""

import os
import time
import sys
from typing import Iterator, IO


DEFAULT_POLL_INTERVAL = 0.1  # seconds


def tail_file(path: str, poll_interval: float = DEFAULT_POLL_INTERVAL) -> Iterator[str]:
    """Yield new lines appended to a file, blocking until more data arrives."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        # Seek to end so we only see new content
        fh.seek(0, os.SEEK_END)
        while True:
            line = fh.readline()
            if line:
                yield line
            else:
                time.sleep(poll_interval)


def tail_stream(stream: IO[str]) -> Iterator[str]:
    """Yield lines from a stream (e.g. stdin), blocking until EOF or interrupt."""
    while True:
        line = stream.readline()
        if line == "":
            # EOF reached
            break
        yield line


def tail_sources(
    paths: list[str],
    follow_stdin: bool = False,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> Iterator[tuple[str, str]]:
    """Interleave lines from multiple tailed files and optionally stdin.

    Yields (source_label, raw_line) tuples.
    Uses a simple round-robin poll across all sources.
    """
    import threading
    import queue

    q: queue.Queue[tuple[str, str]] = queue.Queue()

    def _feed_file(path: str) -> None:
        for line in tail_file(path, poll_interval):
            q.put((path, line))

    def _feed_stdin() -> None:
        for line in tail_stream(sys.stdin):
            q.put(("<stdin>", line))

    threads = []
    for p in paths:
        t = threading.Thread(target=_feed_file, args=(p,), daemon=True)
        t.start()
        threads.append(t)

    if follow_stdin:
        t = threading.Thread(target=_feed_stdin, daemon=True)
        t.start()
        threads.append(t)

    while True:
        try:
            source, line = q.get(timeout=poll_interval)
            yield source, line
        except queue.Empty:
            # Check if all threads have finished
            if all(not t.is_alive() for t in threads):
                break
