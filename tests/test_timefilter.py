"""Tests for logslice.timefilter."""

from datetime import datetime, timezone

import pytest

from logslice.parser import LogRecord
from logslice.timefilter import (
    extract_timestamp,
    filter_by_time,
    make_time_filter,
)


def make_record(data: dict, raw: str = "{}") -> LogRecord:
    return LogRecord(data=data, raw=raw, parse_error=None, source=None)


DT_BASE = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
DT_BEFORE = datetime(2024, 6, 1, 11, 0, 0, tzinfo=timezone.utc)
DT_AFTER = datetime(2024, 6, 1, 13, 0, 0, tzinfo=timezone.utc)


class TestExtractTimestamp:
    def test_reads_timestamp_field(self):
        r = make_record({"timestamp": "2024-06-01T12:00:00Z"})
        dt = extract_timestamp(r)
        assert dt == DT_BASE

    def test_reads_ts_field(self):
        r = make_record({"ts": "2024-06-01T12:00:00Z"})
        assert extract_timestamp(r) == DT_BASE

    def test_reads_time_field(self):
        r = make_record({"time": "2024-06-01T12:00:00.000Z"})
        assert extract_timestamp(r) == DT_BASE

    def test_reads_unix_float(self):
        ts = DT_BASE.timestamp()
        r = make_record({"timestamp": ts})
        dt = extract_timestamp(r)
        assert dt == DT_BASE

    def test_reads_unix_string(self):
        ts = str(DT_BASE.timestamp())
        r = make_record({"timestamp": ts})
        dt = extract_timestamp(r)
        assert dt is not None
        assert abs((dt - DT_BASE).total_seconds()) < 1

    def test_returns_none_when_no_timestamp_field(self):
        r = make_record({"message": "hello"})
        assert extract_timestamp(r) is None

    def test_returns_none_for_unparseable_string(self):
        r = make_record({"timestamp": "not-a-date"})
        assert extract_timestamp(r) is None

    def test_returns_none_for_parse_error_record(self):
        r = LogRecord(data=None, raw="bad", parse_error="err", source=None)
        assert extract_timestamp(r) is None


class TestMakeTimeFilter:
    def test_passes_record_within_window(self):
        r = make_record({"timestamp": "2024-06-01T12:00:00Z"})
        f = make_time_filter(since=DT_BEFORE, until=DT_AFTER)
        assert f(r) is True

    def test_rejects_record_before_since(self):
        r = make_record({"timestamp": "2024-06-01T12:00:00Z"})
        f = make_time_filter(since=DT_AFTER)
        assert f(r) is False

    def test_rejects_record_after_until(self):
        r = make_record({"timestamp": "2024-06-01T12:00:00Z"})
        f = make_time_filter(until=DT_BEFORE)
        assert f(r) is False

    def test_passes_record_with_no_timestamp(self):
        r = make_record({"message": "no time"})
        f = make_time_filter(since=DT_BEFORE, until=DT_AFTER)
        assert f(r) is True

    def test_no_bounds_passes_everything(self):
        r = make_record({"timestamp": "2024-06-01T12:00:00Z"})
        f = make_time_filter()
        assert f(r) is True


class TestFilterByTime:
    def _records(self):
        return [
            make_record({"timestamp": "2024-06-01T11:00:00Z", "msg": "early"}),
            make_record({"timestamp": "2024-06-01T12:00:00Z", "msg": "on-time"}),
            make_record({"timestamp": "2024-06-01T13:00:00Z", "msg": "late"}),
        ]

    def test_filters_outside_window(self):
        records = self._records()
        result = list(filter_by_time(iter(records), since=DT_BASE, until=DT_AFTER))
        assert len(result) == 2

    def test_empty_input_returns_empty(self):
        result = list(filter_by_time(iter([]), since=DT_BEFORE))
        assert result == []

    def test_no_bounds_yields_all(self):
        records = self._records()
        result = list(filter_by_time(iter(records)))
        assert len(result) == 3
