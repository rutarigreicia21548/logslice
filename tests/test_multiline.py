"""Tests for logslice.multiline."""

from __future__ import annotations

import pytest

from logslice.multiline import fold_multiline, is_continuation, multiline_records


# ---------------------------------------------------------------------------
# is_continuation
# ---------------------------------------------------------------------------

class TestIsContinuation:
    def test_matches_default_prefix(self):
        assert is_continuation("  more text", "  ") is True

    def test_no_match_plain_line(self):
        assert is_continuation("plain line", "  ") is False

    def test_custom_prefix(self):
        assert is_continuation("\tcontinued", "\t") is True

    def test_empty_line_with_whitespace_prefix(self):
        assert is_continuation("  ", "  ") is True


# ---------------------------------------------------------------------------
# fold_multiline
# ---------------------------------------------------------------------------

class TestFoldMultiline:
    def test_single_line_passthrough(self):
        result = list(fold_multiline(["hello world"]))
        assert result == ["hello world"]

    def test_continuation_merged(self):
        lines = ["first line", "  continued here"]
        result = list(fold_multiline(lines))
        assert result == ["first line continued here"]

    def test_multiple_continuations(self):
        lines = ["start", "  part two", "  part three"]
        result = list(fold_multiline(lines))
        assert result == ["start part two part three"]

    def test_two_independent_records(self):
        lines = ["record one", "record two"]
        result = list(fold_multiline(lines))
        assert result == ["record one", "record two"]

    def test_mixed_records_and_continuations(self):
        lines = ["rec A", "  cont A", "rec B", "  cont B1", "  cont B2"]
        result = list(fold_multiline(lines))
        assert result == ["rec A cont A", "rec B cont B1 cont B2"]

    def test_strips_trailing_newline(self):
        lines = ["line one\n", "  continuation\n"]
        result = list(fold_multiline(lines))
        assert result == ["line one continuation"]

    def test_custom_join_separator(self):
        lines = ["a", "  b"]
        result = list(fold_multiline(lines, join_with="|"))
        assert result == ["a|b"]

    def test_empty_input(self):
        assert list(fold_multiline([])) == []

    def test_orphan_continuation_emitted(self):
        """A continuation with no preceding line is treated as standalone."""
        lines = ["  orphan"]
        result = list(fold_multiline(lines))
        assert result == ["  orphan"]


# ---------------------------------------------------------------------------
# multiline_records
# ---------------------------------------------------------------------------

class TestMultilineRecords:
    def test_parses_valid_json(self):
        lines = ['{"msg": "hello"}']
        records = list(multiline_records(lines))
        assert len(records) == 1
        assert records[0].data["msg"] == "hello"

    def test_folds_before_parsing(self):
        lines = ['{"msg":', '  "world"}']
        # The folded line becomes '{"msg": "world"}' — valid JSON
        records = list(multiline_records(lines))
        assert len(records) == 1
        assert records[0].data.get("msg") == "world"

    def test_invalid_json_sets_parse_error(self):
        lines = ["not json"]
        records = list(multiline_records(lines))
        assert len(records) == 1
        assert records[0].parse_error is not None

    def test_empty_input_yields_nothing(self):
        assert list(multiline_records([])) == []
