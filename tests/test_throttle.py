"""Tests for logslice.throttle."""

from __future__ import annotations

import time
from typing import List

import pytest

from logslice.parser import LogRecord
from logslice.throttle import _message_key, throttle_records, make_throttle_filter


def make_record(raw: str = '{"message": "hello"}', data: dict | None = None) -> LogRecord:
    return LogRecord(raw=raw, data=data or {"message": "hello"}, parse_error=None)


# ---------------------------------------------------------------------------
# _message_key
# ---------------------------------------------------------------------------

class TestMessageKey:
    def test_uses_field_value(self):
        record = make_record(data={"message": "boom"})
        assert _message_key(record, "message") == "boom"

    def test_falls_back_to_raw_when_missing(self):
        record = make_record(raw="raw-line", data={})
        assert _message_key(record, "message") == "raw-line"

    def test_converts_non_string_to_str(self):
        record = make_record(data={"code": 42})
        assert _message_key(record, "code") == "42"


# ---------------------------------------------------------------------------
# throttle_records
# ---------------------------------------------------------------------------

class TestThrottleRecords:
    def _records(self, messages: List[str]) -> List[LogRecord]:
        return [make_record(data={"message": m}) for m in messages]

    def test_allows_first_occurrence(self):
        records = self._records(["hello"])
        result = list(throttle_records(records, window=60))
        assert len(result) == 1

    def test_suppresses_duplicate_within_window(self):
        records = self._records(["hello", "hello", "hello"])
        result = list(throttle_records(records, window=60))
        assert len(result) == 1

    def test_allows_distinct_messages(self):
        records = self._records(["hello", "world", "hello"])
        result = list(throttle_records(records, window=60))
        # 'hello' is suppressed on second appearance; 'world' passes
        assert len(result) == 2

    def test_max_per_window_allows_multiple(self):
        records = self._records(["hello", "hello", "hello"])
        result = list(throttle_records(records, window=60, max_per_window=2))
        assert len(result) == 2

    def test_empty_input_yields_nothing(self):
        result = list(throttle_records([], window=60))
        assert result == []

    def test_expired_window_resets_count(self):
        """Records seen after the window has elapsed should pass through again."""
        records = self._records(["hello", "hello"])
        seen: List[LogRecord] = []
        import logslice.throttle as mod
        # Patch monotonic to simulate time passing between records
        calls = [0.0, 100.0]  # second call is 100 s later
        idx = 0

        original = time.monotonic

        def fake_monotonic():
            nonlocal idx
            val = calls[idx % len(calls)]
            idx += 1
            return val

        mod.time.monotonic = fake_monotonic  # type: ignore[attr-defined]
        try:
            seen = list(throttle_records(records, window=60))
        finally:
            mod.time.monotonic = original  # type: ignore[attr-defined]

        assert len(seen) == 2

    def test_uses_custom_field(self):
        records = [
            make_record(data={"svc": "api", "message": "a"}),
            make_record(data={"svc": "api", "message": "b"}),
        ]
        result = list(throttle_records(records, window=60, field="svc"))
        assert len(result) == 1


# ---------------------------------------------------------------------------
# make_throttle_filter
# ---------------------------------------------------------------------------

class TestMakeThrottleFilter:
    def test_returns_callable(self):
        f = make_throttle_filter(window=30)
        assert callable(f)

    def test_applied_to_records(self):
        records = [make_record(data={"message": "x"})] * 5
        f = make_throttle_filter(window=60, max_per_window=2)
        result = list(f(records))
        assert len(result) == 2
