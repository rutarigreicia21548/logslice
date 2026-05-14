"""Tests for logslice.parser module."""

import pytest
from logslice.parser import LogRecord, parse_line


class TestParseLine:
    def test_valid_json_object(self):
        record = parse_line('{"level": "info", "msg": "started"}')
        assert record.is_valid
        assert record.data == {"level": "info", "msg": "started"}

    def test_preserves_raw_line(self):
        raw = '{"level": "debug"}'
        record = parse_line(raw)
        assert record.raw == raw

    def test_strips_trailing_newline(self):
        record = parse_line('{"level": "warn"}\n')
        assert record.raw == '{"level": "warn"}'

    def test_invalid_json_sets_parse_error(self):
        record = parse_line("not json at all")
        assert not record.is_valid
        assert record.parse_error is not None
        assert record.data == {}

    def test_json_array_sets_parse_error(self):
        record = parse_line('["a", "b"]')
        assert not record.is_valid
        assert "Expected JSON object" in record.parse_error

    def test_empty_line_sets_parse_error(self):
        record = parse_line("")
        assert not record.is_valid


class TestLogRecordGet:
    def test_existing_key(self):
        record = parse_line('{"service": "auth"}')
        assert record.get("service") == "auth"

    def test_missing_key_returns_default(self):
        record = parse_line('{"service": "auth"}')
        assert record.get("level", "unknown") == "unknown"


class TestLogRecordMatches:
    def test_exact_match(self):
        record = parse_line('{"level": "error", "code": 500}')
        assert record.matches({"code": 500})

    def test_case_insensitive_substring_match(self):
        record = parse_line('{"msg": "Connection refused by host"}')
        assert record.matches({"msg": "connection"})

    def test_no_match_on_wrong_value(self):
        record = parse_line('{"level": "info"}')
        assert not record.matches({"level": "error"})

    def test_no_match_on_missing_key(self):
        record = parse_line('{"level": "info"}')
        assert not record.matches({"service": "auth"})

    def test_empty_filters_always_match(self):
        record = parse_line('{"level": "info"}')
        assert record.matches({})

    def test_multiple_filters_all_must_match(self):
        record = parse_line('{"level": "error", "service": "payments"}')
        assert record.matches({"level": "error", "service": "payments"})
        assert not record.matches({"level": "error", "service": "auth"})
