"""Checkpoint support: persist and resume log stream positions."""

import json
import os
from typing import Dict, Optional

CHECKPOINT_VERSION = 1


def load_checkpoint(path: str) -> Dict[str, int]:
    """Load a checkpoint file and return a mapping of source -> byte offset."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        offsets = data.get("offsets", {})
        if not isinstance(offsets, dict):
            return {}
        return {str(k): int(v) for k, v in offsets.items()}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {}


def save_checkpoint(path: str, offsets: Dict[str, int]) -> None:
    """Persist a mapping of source -> byte offset to a checkpoint file."""
    data = {
        "version": CHECKPOINT_VERSION,
        "offsets": offsets,
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)


def update_checkpoint(offsets: Dict[str, int], source: str, position: int) -> Dict[str, int]:
    """Return a new offsets dict with the given source updated to position."""
    updated = dict(offsets)
    updated[source] = position
    return updated


def get_offset(offsets: Dict[str, int], source: str) -> Optional[int]:
    """Return the stored offset for a source, or None if not present."""
    return offsets.get(source)
