"""Tests for logslice.rotate."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import pytest

from logslice.rotate import (
    _get_inode,
    _get_size,
    has_rotated,
    has_truncated,
    stream_with_rotation,
)


@pytest.fixture()
def tmp_log(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("", encoding="utf-8")
    return p


class TestGetInode:
    def test_returns_integer_for_existing_file(self, tmp_log: Path) -> None:
        assert isinstance(_get_inode(str(tmp_log)), int)

    def test_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        assert _get_inode(str(tmp_path / "ghost.log")) is None


class TestGetSize:
    def test_returns_zero_for_empty_file(self, tmp_log: Path) -> None:
        assert _get_size(str(tmp_log)) == 0

    def test_returns_correct_size(self, tmp_log: Path) -> None:
        tmp_log.write_text("hello\n", encoding="utf-8")
        assert _get_size(str(tmp_log)) == 6

    def test_returns_zero_for_missing_file(self, tmp_path: Path) -> None:
        assert _get_size(str(tmp_path / "nope.log")) == 0


class TestHasRotated:
    def test_false_when_inode_matches(self, tmp_log: Path) -> None:
        inode = _get_inode(str(tmp_log))
        assert has_rotated(str(tmp_log), inode) is False

    def test_true_when_inode_differs(self, tmp_log: Path, tmp_path: Path) -> None:
        old_inode = _get_inode(str(tmp_log))
        new_log = tmp_path / "app2.log"
        new_log.write_text("", encoding="utf-8")
        # Simulate rotation: same path, different inode.
        assert has_rotated(str(new_log), old_inode) is True

    def test_false_when_known_inode_is_none(self, tmp_log: Path) -> None:
        assert has_rotated(str(tmp_log), None) is False


class TestHasTruncated:
    def test_false_when_size_unchanged(self, tmp_log: Path) -> None:
        tmp_log.write_text("data\n", encoding="utf-8")
        assert has_truncated(str(tmp_log), 5) is False

    def test_true_when_file_shrinks(self, tmp_log: Path) -> None:
        tmp_log.write_text("data\n", encoding="utf-8")
        assert has_truncated(str(tmp_log), 100) is True


class TestStreamWithRotation:
    def test_yields_existing_lines(self, tmp_log: Path) -> None:
        tmp_log.write_text("line1\nline2\n", encoding="utf-8")
        lines = list(stream_with_rotation(str(tmp_log), poll_interval=0, max_iterations=1))
        assert lines == ["line1\n", "line2\n"]

    def test_empty_file_yields_nothing(self, tmp_log: Path) -> None:
        lines = list(stream_with_rotation(str(tmp_log), poll_interval=0, max_iterations=1))
        assert lines == []

    def test_missing_file_yields_nothing(self, tmp_path: Path) -> None:
        path = str(tmp_path / "missing.log")
        lines = list(stream_with_rotation(path, poll_interval=0, max_iterations=1))
        assert lines == []

    def test_rereads_after_truncation(self, tmp_log: Path) -> None:
        tmp_log.write_text("old\n", encoding="utf-8")
        results: list[str] = []
        gen = stream_with_rotation(str(tmp_log), poll_interval=0, max_iterations=3)
        results.append(next(gen))  # reads "old\n" on first iteration
        # Truncate the file.
        tmp_log.write_text("new\n", encoding="utf-8")
        collected = list(gen)
        assert results[0] == "old\n"
        assert "new\n" in collected
