"""Tests for logslice.ratelimit."""

import time
import pytest
from logslice.parser import LogRecord
from logslice.ratelimit import rate_limit_records, burst_limit_records


def make_record(msg: str = "hello") -> LogRecord:
    return LogRecord(raw=f'{{"message": "{msg}"}}', data={"message": msg})


class TestRateLimitRecords:
    def test_yields_all_records(self):
        records = [make_record(str(i)) for i in range(5)]
        result = list(rate_limit_records(records, max_per_second=1000.0))
        assert len(result) == 5

    def test_preserves_order(self):
        records = [make_record(str(i)) for i in range(4)]
        result = list(rate_limit_records(records, max_per_second=1000.0))
        for original, returned in zip(records, result):
            assert original is returned

    def test_empty_input_yields_nothing(self):
        result = list(rate_limit_records([], max_per_second=10.0))
        assert result == []

    def test_raises_on_zero_rate(self):
        with pytest.raises(ValueError, match="max_per_second"):
            list(rate_limit_records([make_record()], max_per_second=0))

    def test_raises_on_negative_rate(self):
        with pytest.raises(ValueError, match="max_per_second"):
            list(rate_limit_records([make_record()], max_per_second=-5.0))

    def test_enforces_delay_between_records(self):
        records = [make_record(str(i)) for i in range(3)]
        start = time.monotonic()
        list(rate_limit_records(records, max_per_second=50.0))
        elapsed = time.monotonic() - start
        # 3 records at 50/s => at least ~40ms gap for 2 intervals
        assert elapsed >= 0.03


class TestBurstLimitRecords:
    def test_allows_records_within_burst(self):
        records = [make_record(str(i)) for i in range(5)]
        result = list(burst_limit_records(records, burst_size=5, window_seconds=10.0))
        assert len(result) == 5

    def test_drops_records_exceeding_burst(self):
        records = [make_record(str(i)) for i in range(10)]
        result = list(burst_limit_records(records, burst_size=3, window_seconds=10.0))
        assert len(result) == 3

    def test_empty_input_yields_nothing(self):
        result = list(burst_limit_records([], burst_size=5))
        assert result == []

    def test_raises_on_zero_burst_size(self):
        with pytest.raises(ValueError, match="burst_size"):
            list(burst_limit_records([make_record()], burst_size=0))

    def test_raises_on_negative_burst_size(self):
        with pytest.raises(ValueError, match="burst_size"):
            list(burst_limit_records([make_record()], burst_size=-1))

    def test_raises_on_zero_window(self):
        with pytest.raises(ValueError, match="window_seconds"):
            list(burst_limit_records([make_record()], burst_size=5, window_seconds=0))

    def test_new_window_resets_budget(self):
        records = [make_record(str(i)) for i in range(4)]
        # burst_size=2, window=0.05s — sleep between batches to open a new window
        def slow_records():
            for r in records[:2]:
                yield r
            time.sleep(0.12)
            for r in records[2:]:
                yield r

        result = list(burst_limit_records(slow_records(), burst_size=2, window_seconds=0.05))
        assert len(result) == 4
