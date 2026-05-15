"""Tests for logslice.context and logslice.cli_context."""

import argparse
import pytest

from logslice.parser import LogRecord
from logslice.context import context_window
from logslice.cli_context import add_context_args, apply_context


def make_record(msg: str, level: str = "info") -> LogRecord:
    raw = f'{{"message": "{msg}", "level": "{level}"}}'
    return LogRecord(raw=raw, data={"message": msg, "level": level}, parse_error=None)


is_error = lambda r: r.data.get("level") == "error"


class TestContextWindow:
    def _records(self):
        return [
            make_record("a"),
            make_record("b"),
            make_record("c", "error"),
            make_record("d"),
            make_record("e"),
        ]

    def test_no_context_yields_only_matches(self):
        result = list(context_window(self._records(), is_error, before=0, after=0))
        assert len(result) == 1
        assert result[0].data["message"] == "c"

    def test_before_includes_preceding_records(self):
        result = list(context_window(self._records(), is_error, before=2, after=0))
        messages = [r.data["message"] for r in result]
        assert messages == ["a", "b", "c"]

    def test_after_includes_following_records(self):
        result = list(context_window(self._records(), is_error, before=0, after=2))
        messages = [r.data["message"] for r in result]
        assert messages == ["c", "d", "e"]

    def test_before_and_after(self):
        result = list(context_window(self._records(), is_error, before=1, after=1))
        messages = [r.data["message"] for r in result]
        assert messages == ["b", "c", "d"]

    def test_no_duplicates_when_windows_overlap(self):
        records = [
            make_record("a", "error"),
            make_record("b", "error"),
            make_record("c"),
        ]
        result = list(context_window(records, is_error, before=0, after=1))
        messages = [r.data["message"] for r in result]
        # 'b' is both the after-context of 'a' and a match itself — emitted once
        assert messages.count("b") == 1

    def test_empty_iterable_returns_nothing(self):
        result = list(context_window([], is_error, before=2, after=2))
        assert result == []

    def test_negative_before_raises(self):
        with pytest.raises(ValueError):
            list(context_window(self._records(), is_error, before=-1, after=0))

    def test_negative_after_raises(self):
        with pytest.raises(ValueError):
            list(context_window(self._records(), is_error, before=0, after=-1))

    def test_before_larger_than_available_records(self):
        result = list(context_window(self._records(), is_error, before=10, after=0))
        messages = [r.data["message"] for r in result]
        assert "a" in messages and "c" in messages


class TestCliContext:
    def _parser(self):
        p = argparse.ArgumentParser()
        add_context_args(p)
        return p

    def test_defaults_are_zero(self):
        args = self._parser().parse_args([])
        assert args.before == 0
        assert args.after == 0
        assert args.context is None

    def test_before_flag(self):
        args = self._parser().parse_args(["-B", "3"])
        assert args.before == 3

    def test_after_flag(self):
        args = self._parser().parse_args(["-A", "2"])
        assert args.after == 2

    def test_context_flag_sets_both(self):
        args = self._parser().parse_args(["-C", "4"])
        assert args.context == 4

    def test_apply_context_passthrough_when_zero(self):
        records = [make_record("x", "error"), make_record("y")]
        args = self._parser().parse_args([])
        result = list(apply_context(records, args, is_error))
        # passthrough — only the match
        assert len(result) == 2  # no filtering applied in passthrough

    def test_apply_context_uses_context_flag(self):
        records = [
            make_record("a"),
            make_record("b", "error"),
            make_record("c"),
            make_record("d"),
        ]
        args = self._parser().parse_args(["-C", "1"])
        result = list(apply_context(records, args, is_error))
        messages = [r.data["message"] for r in result]
        assert messages == ["a", "b", "c"]
