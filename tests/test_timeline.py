"""Tests for logslice.timeline."""

from __future__ import annotations

import pytest

from logslice.parser import LogRecord
from logslice.timeline import bucket_records, iter_timeline, timeline_counts, _bucket_key


def make_record(ts: float | None = None, **fields) -> LogRecord:
    data = dict(fields)
    if ts is not None:
        data["timestamp"] = ts
    raw = str(data)
    return LogRecord(raw=raw, data=data, parse_error=None)


class TestBucketKey:
    def test_aligns_to_interval(self):
        assert _bucket_key(65.0, 60.0) == 60.0

    def test_exact_boundary(self):
        assert _bucket_key(120.0, 60.0) == 120.0

    def test_small_interval(self):
        assert _bucket_key(7.5, 5.0) == 5.0

    def test_zero_offset(self):
        assert _bucket_key(0.0, 60.0) == 0.0


class TestBucketRecords:
    def test_groups_into_correct_buckets(self):
        records = [
            make_record(ts=10.0),
            make_record(ts=30.0),
            make_record(ts=70.0),
        ]
        result = bucket_records(records, interval=60.0)
        assert set(result.keys()) == {0.0, 60.0}
        assert len(result[0.0]) == 2
        assert len(result[60.0]) == 1

    def test_skips_records_without_timestamp(self):
        records = [make_record(), make_record(ts=5.0)]
        result = bucket_records(records, interval=60.0)
        assert list(result.keys()) == [0.0]
        assert len(result[0.0]) == 1

    def test_empty_input_returns_empty_dict(self):
        assert bucket_records([], interval=60.0) == {}

    def test_result_is_sorted(self):
        records = [make_record(ts=200.0), make_record(ts=10.0)]
        keys = list(bucket_records(records, interval=60.0).keys())
        assert keys == sorted(keys)


class TestTimelineCounts:
    def test_returns_count_per_bucket(self):
        records = [
            make_record(ts=5.0),
            make_record(ts=10.0),
            make_record(ts=90.0),
        ]
        counts = timeline_counts(records, interval=60.0)
        assert counts == [(0.0, 2), (60.0, 1)]

    def test_empty_input(self):
        assert timeline_counts([], interval=60.0) == []


class TestIterTimeline:
    def test_yields_tuples(self):
        records = [make_record(ts=5.0), make_record(ts=65.0)]
        result = list(iter_timeline(records, interval=60.0))
        assert len(result) == 2
        ts0, recs0 = result[0]
        assert ts0 == 0.0
        assert len(recs0) == 1

    def test_chronological_order(self):
        records = [make_record(ts=180.0), make_record(ts=30.0)]
        keys = [ts for ts, _ in iter_timeline(records, interval=60.0)]
        assert keys == sorted(keys)
