"""Log rotation detection and file re-open support."""

from __future__ import annotations

import os
import time
from typing import Iterator, Optional


def _get_inode(path: str) -> Optional[int]:
    """Return the inode number for a file, or None if it cannot be read."""
    try:
        return os.stat(path).st_ino
    except OSError:
        return None


def _get_size(path: str) -> int:
    """Return the current file size in bytes, or 0 on error."""
    try:
        return os.stat(path).st_size
    except OSError:
        return 0


def has_rotated(path: str, known_inode: Optional[int]) -> bool:
    """Return True if the file at *path* has a different inode than *known_inode*."""
    if known_inode is None:
        return False
    current = _get_inode(path)
    return current is not None and current != known_inode


def has_truncated(path: str, known_offset: int) -> bool:
    """Return True if the file is smaller than *known_offset* (truncation)."""
    return _get_size(path) < known_offset


def stream_with_rotation(
    path: str,
    poll_interval: float = 0.25,
    max_iterations: Optional[int] = None,
) -> Iterator[str]:
    """Yield lines from *path*, re-opening the file when rotation is detected.

    Rotation is detected by inode change or file truncation.  The generator
    runs indefinitely unless *max_iterations* is set (useful for testing).
    """
    inode: Optional[int] = None
    offset: int = 0
    iterations = 0

    while True:
        if max_iterations is not None:
            if iterations >= max_iterations:
                break
            iterations += 1

        if not os.path.exists(path):
            time.sleep(poll_interval)
            continue

        current_inode = _get_inode(path)

        if has_rotated(path, inode) or has_truncated(path, offset):
            # File was rotated or truncated — start from the beginning.
            offset = 0
            inode = current_inode

        if inode is None:
            inode = current_inode

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(offset)
                for line in fh:
                    yield line
                offset = fh.tell()
        except OSError:
            pass

        time.sleep(poll_interval)
