"""Tests for logslice.filter."""

import pytest
from logslice.parser import parse_line
from logslice.filter import (
    make_field_filter,
    make_level_filter,
    make_service_filter,
    build_filter,
    apply_filter,
)


def make_record(raw: str):
    return parse_line(raw)


INFO_LINE = '{"level": "info", "service": "api", "msg": "started"}'
ERROR_LINE = '{"level": "error", "service": "worker", "msg": "crashed"}'
DEBUG_LINE = '{"level": "debug", "service": "api", "msg": "verbose"}'
WARN_LINE = '{"level": "warn", "service": "db", "msg": "slow query"}'
INVALID_LINE = "not json at all"


class TestFieldFilter:
    def test_matches_exact_value(self):
        record = make_record(INFO_LINE)
        f = make_field_filter("service", "api")
        assert f(record) is True

    def test_no_match_different_value(self):
        record = make_record(INFO_LINE)
        f = make_field_filter("service", "worker")
        assert f(record) is False

    def test_missing_field_returns_false(self):
        record = make_record(INFO_LINE)
        f = make_field_filter("nonexistent", "value")
        assert f(record) is False

    def test_invalid_record_returns_false(self):
        record = make_record(INVALID_LINE)
        f = make_field_filter("level", "info")
        assert f(record) is False


class TestLevelFilter:
    def test_exact_level_matches(self):
        record = make_record(INFO_LINE)
        f = make_level_filter("info")
        assert f(record) is True

    def test_higher_level_matches(self):
        record = make_record(ERROR_LINE)
        f = make_level_filter("info")
        assert f(record) is True

    def test_lower_level_excluded(self):
        record = make_record(DEBUG_LINE)
        f = make_level_filter("info")
        assert f(record) is False

    def test_warn_normalised_to_warning(self):
        record = make_record(WARN_LINE)
        f = make_level_filter("warning")
        assert f(record) is True

    def test_unknown_level_falls_back_to_exact(self):
        record = make_record('{"level": "trace"}' )
        f = make_level_filter("trace")
        assert f(record) is True


class TestBuildAndApplyFilter:
    def test_empty_predicates_passes_all(self):
        records = [make_record(l) for l in [INFO_LINE, ERROR_LINE, DEBUG_LINE]]
        combined = build_filter([])
        assert apply_filter(records, combined) == records

    def test_combined_and_semantics(self):
        records = [make_record(l) for l in [INFO_LINE, ERROR_LINE, DEBUG_LINE]]
        combined = build_filter([
            make_service_filter("api"),
            make_level_filter("info"),
        ])
        result = apply_filter(records, combined)
        assert len(result) == 1
        assert result[0]["data"]["msg"] == "started"

    def test_apply_filter_returns_matching_subset(self):
        records = [make_record(l) for l in [INFO_LINE, ERROR_LINE]]
        result = apply_filter(records, make_service_filter("worker"))
        assert len(result) == 1
