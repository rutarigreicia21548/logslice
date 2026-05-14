"""Tests for logslice.formatter."""

import pytest
from logslice.parser import LogRecord
from logslice.formatter import format_pretty, format_json, format_record


def make_record(raw: str, data: dict = None, error: str = None) -> LogRecord:
    return LogRecord(raw=raw, data=data or {}, parse_error=error)


class TestFormatPretty:
    def test_renders_message(self):
        r = make_record('{"msg": "hello"}', {"msg": "hello"})
        out = format_pretty(r, color=False)
        assert "hello" in out

    def test_renders_level(self):
        r = make_record('{}', {"level": "error", "msg": "boom"})
        out = format_pretty(r, color=False)
        assert "ERROR" in out

    def test_renders_service(self):
        r = make_record('{}', {"service": "api", "msg": "ok"})
        out = format_pretty(r, color=False)
        assert "[api]" in out

    def test_renders_timestamp(self):
        r = make_record('{}', {"timestamp": "2024-01-01T00:00:00Z", "msg": "t"})
        out = format_pretty(r, color=False)
        assert "2024-01-01" in out

    def test_raw_fallback_on_parse_error(self):
        r = make_record("not json", error="invalid JSON")
        out = format_pretty(r, color=False)
        assert "[raw]" in out
        assert "not json" in out

    def test_color_codes_included_when_enabled(self):
        r = make_record('{}', {"level": "INFO", "msg": "hi"})
        out = format_pretty(r, color=True)
        assert "\033[" in out

    def test_no_color_codes_when_disabled(self):
        r = make_record('{}', {"level": "INFO", "msg": "hi"})
        out = format_pretty(r, color=False)
        assert "\033[" not in out

    def test_alternate_field_names(self):
        r = make_record('{}', {"severity": "warn", "app": "svc", "time": "T", "message": "m"})
        out = format_pretty(r, color=False)
        assert "WARN" in out
        assert "[svc]" in out
        assert "m" in out


class TestFormatJson:
    def test_valid_record_returns_json(self):
        r = make_record('{}', {"level": "info", "msg": "hi"})
        out = format_json(r)
        assert '"level"' in out
        assert '"msg"' in out

    def test_parse_error_returns_raw(self):
        r = make_record("bad line", error="err")
        assert format_json(r) == "bad line"


class TestFormatRecord:
    def test_dispatches_pretty(self):
        r = make_record('{}', {"msg": "x"})
        out = format_record(r, fmt="pretty", color=False)
        assert "x" in out

    def test_dispatches_json(self):
        r = make_record('{}', {"msg": "x"})
        out = format_record(r, fmt="json")
        assert '{' in out

    def test_default_is_pretty(self):
        r = make_record('{}', {"msg": "y"})
        out = format_record(r, color=False)
        assert "y" in out
