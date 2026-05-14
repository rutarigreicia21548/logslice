"""Tests for logslice.sampling."""

from __future__ import annotations

import pytest

from logslice.parser import LogRecord
from logslice.sampling import _hash_record, every_nth, sample_records


def make_record(raw: str = '{"msg": "hello"}', data: dict | None = None) -> LogRecord:
    return LogRecord(raw=raw, data=data or {"msg": "hello"}, parse_error=None)


# ---------------------------------------------------------------------------
# _hash_record
# ---------------------------------------------------------------------------

class TestHashRecord:
    def test_returns_integer(self):
        record = make_record()
        assert isinstance(_hash_record(record, None), int)

    def test_stable_across_calls(self):
        record = make_record()
        assert _hash_record(record, None) == _hash_record(record, None)

    def test_uses_field_when_provided(self):
        record = make_record(data={"msg": "hello", "trace": "abc"})
        h1 = _hash_record(record, "trace")
        h2 = _hash_record(record, "msg")
        assert h1 != h2

    def test_falls_back_to_raw_for_missing_field(self):
        record = make_record(raw='{"msg": "hi"}')
        h_field = _hash_record(record, "nonexistent")
        h_raw = _hash_record(record, None)
        assert h_field == h_raw


# ---------------------------------------------------------------------------
# sample_records
# ---------------------------------------------------------------------------

class TestSampleRecords:
    def _make_records(self, n: int) -> list[LogRecord]:
        return [make_record(raw=f'{{"i": {i}}}', data={"i": i}) for i in range(n)]

    def test_rate_one_keeps_all(self):
        records = self._make_records(20)
        result = list(sample_records(records, rate=1.0))
        assert result == records

    def test_rate_zero_drops_all(self):
        records = self._make_records(20)
        result = list(sample_records(records, rate=0.0))
        assert result == []

    def test_partial_rate_reduces_count(self):
        records = self._make_records(1000)
        result = list(sample_records(records, rate=0.1))
        # Allow generous tolerance for hash distribution.
        assert 50 <= len(result) <= 200

    def test_deterministic_output(self):
        records = self._make_records(200)
        r1 = list(sample_records(records, rate=0.5))
        r2 = list(sample_records(records, rate=0.5))
        assert r1 == r2

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError, match="rate"):
            list(sample_records([], rate=1.5))

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            list(sample_records([], rate=-0.1))

    def test_field_keyed_sampling(self):
        # Records sharing the same trace id should be kept/dropped together.
        records = [
            make_record(raw=f'{{"trace": "aaa", "seq": {i}}}', data={"trace": "aaa", "seq": i})
            for i in range(10)
        ]
        result = list(sample_records(records, rate=0.5, field="trace"))
        # All-or-nothing for the same field value.
        assert len(result) in (0, 10)


# ---------------------------------------------------------------------------
# every_nth
# ---------------------------------------------------------------------------

class TestEveryNth:
    def test_every_second(self):
        records = [make_record(raw=f'{{"i": {i}}}', data={"i": i}) for i in range(6)]
        result = list(every_nth(records, n=2))
        assert [r.data["i"] for r in result] == [1, 3, 5]

    def test_every_first_returns_all(self):
        records = [make_record() for _ in range(5)]
        assert list(every_nth(records, 1)) == records

    def test_n_larger_than_count(self):
        records = [make_record() for _ in range(3)]
        assert list(every_nth(records, 10)) == []

    def test_invalid_n_raises(self):
        with pytest.raises(ValueError, match="n must be"):
            list(every_nth([], n=0))

    def test_empty_input(self):
        assert list(every_nth([], n=3)) == []
