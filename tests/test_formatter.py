"""Tests for logslice.formatter."""

from __future__ import annotations

import json
import pytest

from logslice.parser import LogRecord
from logslice.formatter import format_pretty, format_json, format_record
from logslice.highlight import ANSI_COLORS, ANSI_RESET


def make_record(data: dict | None = None, raw: str = "") -> LogRecord:
    if data is not None and not raw:
        raw = json.dumps(data)
    return LogRecord(raw=raw, data=data, parse_error=None)


class TestFormatPretty:
    def test_renders_message(self):
        rec = make_record({"msg": "hello world"})
        result = format_pretty(rec, color=False)
        assert "hello world" in result

    def test_renders_level(self):
        rec = make_record({"level": "info", "msg": "ok"})
        result = format_pretty(rec, color=False)
        assert "INFO" in result

    def test_renders_service(self):
        rec = make_record({"service": "auth", "msg": "started"})
        result = format_pretty(rec, color=False)
        assert "[auth]" in result

    def test_renders_timestamp(self):
        rec = make_record({"timestamp": "2024-01-01T00:00:00Z", "msg": "x"})
        result = format_pretty(rec, color=False)
        assert "2024-01-01T00:00:00Z" in result

    def test_renders_extra_fields(self):
        rec = make_record({"msg": "hi", "request_id": "abc123"})
        result = format_pretty(rec, color=False)
        assert "request_id=abc123" in result

    def test_skips_known_fields_in_extras(self):
        rec = make_record({"msg": "hi", "level": "info", "extra": "yes"})
        result = format_pretty(rec, color=False)
        # 'msg' and 'level' should not appear as key=value extras
        assert "msg=" not in result
        assert "level=" not in result

    def test_color_codes_present_when_enabled(self):
        rec = make_record({"level": "error", "msg": "boom"})
        result = format_pretty(rec, color=True)
        assert ANSI_COLORS["red"] in result

    def test_no_color_codes_when_disabled(self):
        rec = make_record({"level": "error", "msg": "boom"})
        result = format_pretty(rec, color=False)
        assert "\033[" not in result

    def test_handles_none_data(self):
        rec = make_record(raw="not json")
        rec = LogRecord(raw="not json", data=None, parse_error="invalid")
        # Should not raise
        result = format_pretty(rec, color=False)
        assert isinstance(result, str)

    def test_uses_alternative_timestamp_keys(self):
        rec = make_record({"ts": "12345", "msg": "x"})
        result = format_pretty(rec, color=False)
        assert "12345" in result

    def test_uses_alternative_message_keys(self):
        rec = make_record({"message": "alt msg"})
        result = format_pretty(rec, color=False)
        assert "alt msg" in result


class TestFormatJson:
    def test_returns_compact_json(self):
        data = {"level": "info", "msg": "hello"}
        rec = make_record(data)
        result = format_json(rec)
        assert json.loads(result) == data

    def test_no_spaces_in_output(self):
        rec = make_record({"a": 1, "b": 2})
        result = format_json(rec)
        assert " " not in result

    def test_fallback_to_raw_when_no_data(self):
        rec = LogRecord(raw="raw line\n", data=None, parse_error="err")
        result = format_json(rec)
        assert result == "raw line"


class TestFormatRecord:
    def test_dispatches_to_pretty(self):
        rec = make_record({"msg": "hi"})
        result = format_record(rec, fmt="pretty", color=False)
        assert "hi" in result

    def test_dispatches_to_json(self):
        rec = make_record({"msg": "hi"})
        result = format_record(rec, fmt="json")
        assert json.loads(result)["msg"] == "hi"

    def test_defaults_to_pretty(self):
        rec = make_record({"msg": "default"})
        result = format_record(rec, color=False)
        assert "default" in result
