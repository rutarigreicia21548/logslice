"""Tests for logslice.truncate and logslice.cli_truncate."""

import argparse
from typing import Iterator

import pytest

from logslice.parser import LogRecord
from logslice.truncate import (
    DEFAULT_MAX_LENGTH,
    truncate_value,
    truncate_field,
    truncate_fields,
    truncate_records,
)
from logslice.cli_truncate import add_truncate_args, apply_truncation


def make_record(data: dict | None = None, raw: str = "{}") -> LogRecord:
    return LogRecord(raw=raw, data=data or {}, parse_error=None)


class TestTruncateValue:
    def test_short_string_unchanged(self):
        assert truncate_value("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert truncate_value("hello", 5) == "hello"

    def test_long_string_trimmed_with_ellipsis(self):
        result = truncate_value("abcdefghij", 6)
        assert result == "abc..."
        assert len(result) == 6

    def test_non_string_returned_as_is(self):
        assert truncate_value(42, 5) == 42  # type: ignore[arg-type]

    def test_uses_default_max_length(self):
        long_str = "x" * 300
        result = truncate_value(long_str)
        assert len(result) == DEFAULT_MAX_LENGTH
        assert result.endswith("...")


class TestTruncateField:
    def test_truncates_named_field(self):
        record = make_record({"msg": "a" * 50})
        result = truncate_field(record, "msg", max_length=10)
        assert len(result.data["msg"]) == 10
        assert result.data["msg"].endswith("...")

    def test_leaves_other_fields_intact(self):
        record = make_record({"msg": "a" * 50, "level": "info"})
        result = truncate_field(record, "msg", max_length=10)
        assert result.data["level"] == "info"

    def test_missing_field_returns_original(self):
        record = make_record({"level": "info"})
        result = truncate_field(record, "msg", max_length=10)
        assert result is record

    def test_short_value_returns_original(self):
        record = make_record({"msg": "short"})
        result = truncate_field(record, "msg", max_length=100)
        assert result is record

    def test_non_string_field_unchanged(self):
        record = make_record({"code": 12345})
        result = truncate_field(record, "code", max_length=3)
        assert result.data["code"] == 12345


class TestTruncateFields:
    def test_truncates_multiple_fields(self):
        record = make_record({"msg": "a" * 50, "detail": "b" * 50})
        result = truncate_fields(record, ["msg", "detail"], max_length=10)
        assert len(result.data["msg"]) == 10
        assert len(result.data["detail"]) == 10

    def test_empty_field_list_returns_original(self):
        record = make_record({"msg": "a" * 50})
        result = truncate_fields(record, [], max_length=10)
        assert result is record


class TestTruncateRecords:
    def test_yields_truncated_records(self):
        records = [make_record({"msg": "x" * 50}) for _ in range(3)]
        results = list(truncate_records(iter(records), ["msg"], max_length=10))
        assert all(len(r.data["msg"]) == 10 for r in results)

    def test_empty_iterator(self):
        assert list(truncate_records(iter([]), ["msg"])) == []


class TestCliTruncate:
    def _parser(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser()
        add_truncate_args(p)
        return p

    def test_default_truncate_fields_empty(self):
        args = self._parser().parse_args([])
        assert args.truncate_fields == []

    def test_default_max_length(self):
        args = self._parser().parse_args([])
        assert args.max_length == DEFAULT_MAX_LENGTH

    def test_truncate_field_flag(self):
        args = self._parser().parse_args(["--truncate-field", "msg"])
        assert "msg" in args.truncate_fields

    def test_multiple_truncate_fields(self):
        args = self._parser().parse_args(
            ["--truncate-field", "msg", "--truncate-field", "detail"]
        )
        assert args.truncate_fields == ["msg", "detail"]

    def test_apply_truncation_no_fields_passthrough(self):
        record = make_record({"msg": "a" * 50})
        args = argparse.Namespace(truncate_fields=[], max_length=10)
        result = list(apply_truncation(iter([record]), args))
        assert result[0].data["msg"] == "a" * 50

    def test_apply_truncation_with_fields(self):
        record = make_record({"msg": "a" * 50})
        args = argparse.Namespace(truncate_fields=["msg"], max_length=10)
        result = list(apply_truncation(iter([record]), args))
        assert len(result[0].data["msg"]) == 10
