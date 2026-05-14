"""Tests for logslice.tail — file and stream tailing utilities."""

import io
import os
import tempfile
import threading
import time

import pytest

from logslice.tail import tail_stream, tail_sources


class TestTailStream:
    def test_yields_all_lines(self):
        stream = io.StringIO("line1\nline2\nline3\n")
        result = list(tail_stream(stream))
        assert result == ["line1\n", "line2\n", "line3\n"]

    def test_empty_stream_returns_nothing(self):
        stream = io.StringIO("")
        result = list(tail_stream(stream))
        assert result == []

    def test_stops_at_eof(self):
        stream = io.StringIO("only\n")
        lines = list(tail_stream(stream))
        assert len(lines) == 1


class TestTailSources:
    def _write_lines(self, path: str, lines: list[str], delay: float = 0.0) -> None:
        """Append lines to a file, optionally with a delay."""
        def _worker():
            time.sleep(delay)
            with open(path, "a", encoding="utf-8") as fh:
                for line in lines:
                    fh.write(line + "\n")
                    fh.flush()
                    time.sleep(0.01)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def test_single_file_yields_new_lines(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            path = f.name

        try:
            t = self._write_lines(path, ['{"msg": "hello"}', '{"msg": "world"}'])
            collected = []
            for source, line in tail_sources([path], poll_interval=0.05):
                collected.append((source, line.strip()))
                if len(collected) >= 2:
                    break
            t.join(timeout=2)
            assert len(collected) == 2
            assert all(src == path for src, _ in collected)
        finally:
            os.unlink(path)

    def test_source_label_matches_path(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            path = f.name

        try:
            self._write_lines(path, ['{"x": 1}'])
            for source, _ in tail_sources([path], poll_interval=0.05):
                assert source == path
                break
        finally:
            os.unlink(path)
