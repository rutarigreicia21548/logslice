"""CLI helpers for checkpoint (resume) support."""

import argparse
from typing import Dict, Optional

from logslice.checkpoint import load_checkpoint, save_checkpoint, update_checkpoint


def add_checkpoint_args(parser: argparse.ArgumentParser) -> None:
    """Register --checkpoint flag on an argument parser."""
    parser.add_argument(
        "--checkpoint",
        metavar="FILE",
        default=None,
        help="Path to checkpoint file for resuming streams from last position.",
    )


def load_offsets(args: argparse.Namespace) -> Dict[str, int]:
    """Return stored offsets if a checkpoint path is configured, else empty dict."""
    if not args.checkpoint:
        return {}
    return load_checkpoint(args.checkpoint)


def persist_offsets(args: argparse.Namespace, offsets: Dict[str, int]) -> None:
    """Write offsets back to the checkpoint file if one is configured."""
    if args.checkpoint:
        save_checkpoint(args.checkpoint, offsets)


def record_position(
    args: argparse.Namespace,
    offsets: Dict[str, int],
    source: str,
    position: int,
) -> Dict[str, int]:
    """Update in-memory offsets and, if checkpoint is configured, persist them."""
    updated = update_checkpoint(offsets, source, position)
    persist_offsets(args, updated)
    return updated
