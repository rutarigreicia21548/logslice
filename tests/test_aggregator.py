"""Tests for logslice.aggregator."""

import pytest
from logslice.parser import LogRecord
from logslice.aggregator import (
    count_by_field,
    count_by_level,
    count_by_service,
    summarize,
    group_by_field,
)


def make_record(data: dict) -> LogRecord:
    import json
    raw = json.dumps(data)
    return LogRecord(raw=raw, data=data, parse_error=None)


RECORDS = [
    make_record({"level": "info", "service": "api", "message": "started"}),
    make_record({"level": "info", "service": "worker", "message": "processing"}),
    make_record({"level": "error", "service": "api", "message": "failed"}),
    make_record({"level": "warn", "service": "api", "message": "slow"}),
    make_record({"level": "error", "service": "worker", "message": "crash"}),
]


class TestCountByField:
    def test_counts_known_field(self):
        result = count_by_field(RECORDS, "level")
        assert result["info"] == 2
        assert result["error"] == 2
        assert result["warn"] == 1

    def test_missing_field_uses_placeholder(self):
        records = [make_record({"message": "no level"})]
        result = count_by_field(records, "level")
        assert result["<missing>"] == 1

    def test_empty_iterable_returns_empty_counter(self):
        result = count_by_field([], "level")
        assert len(result) == 0


class TestCountByLevel:
    def test_delegates_to_level_field(self):
        result = count_by_level(RECORDS)
        assert result["error"] == 2
        assert result["info"] == 2


class TestCountByService:
    def test_delegates_to_service_field(self):
        result = count_by_service(RECORDS)
        assert result["api"] == 3
        assert result["worker"] == 2


class TestSummarize:
    def test_total_count(self):
        summary = summarize(RECORDS)
        assert summary["total"] == 5

    def test_by_level_keys(self):
        summary = summarize(RECORDS)
        assert set(summary["by_level"].keys()) == {"info", "error", "warn"}

    def test_by_service_keys(self):
        summary = summarize(RECORDS)
        assert set(summary["by_service"].keys()) == {"api", "worker"}

    def test_empty_records(self):
        summary = summarize([])
        assert summary["total"] == 0
        assert summary["by_level"] == {}
        assert summary["by_service"] == {}


class TestGroupByField:
    def test_groups_correctly(self):
        groups = group_by_field(RECORDS, "service")
        assert len(groups["api"]) == 3
        assert len(groups["worker"]) == 2

    def test_missing_field_grouped_under_placeholder(self):
        records = [make_record({"message": "no service"})]
        groups = group_by_field(records, "service")
        assert "<missing>" in groups
        assert len(groups["<missing>"]) == 1
