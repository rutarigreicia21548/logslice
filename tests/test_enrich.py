"""Tests for logslice.enrich."""

import pytest
from logslice.parser import LogRecord
from logslice.enrich import (
    enrich_with_static,
    enrich_with_computed,
    enrich_records,
)


def make_record(data=None, raw="{}"):
    return LogRecord(data=data or {}, raw=raw, parse_error=None)


class TestEnrichWithStatic:
    def test_adds_missing_field(self):
        r = make_record({"msg": "hello"})
        result = enrich_with_static(r, "env", "prod")
        assert result.data["env"] == "prod"

    def test_does_not_overwrite_existing_field(self):
        r = make_record({"env": "staging"})
        result = enrich_with_static(r, "env", "prod")
        assert result.data["env"] == "staging"

    def test_preserves_other_fields(self):
        r = make_record({"msg": "hi", "level": "info"})
        result = enrich_with_static(r, "env", "prod")
        assert result.data["msg"] == "hi"
        assert result.data["level"] == "info"

    def test_raw_unchanged(self):
        r = make_record({"msg": "hi"}, raw='{"msg":"hi"}')
        result = enrich_with_static(r, "env", "prod")
        assert result.raw == '{"msg":"hi"}'

    def test_returns_new_record_not_same(self):
        r = make_record({"msg": "hi"})
        result = enrich_with_static(r, "env", "prod")
        assert result is not r


class TestEnrichWithComputed:
    def test_adds_computed_field(self):
        r = make_record({"level": "error"})
        result = enrich_with_computed(r, "severity", lambda rec: rec.data.get("level", "").upper())
        assert result.data["severity"] == "ERROR"

    def test_none_return_skips_field(self):
        r = make_record({"msg": "hi"})
        result = enrich_with_computed(r, "severity", lambda rec: None)
        assert "severity" not in result.data

    def test_does_not_overwrite_existing(self):
        r = make_record({"severity": "LOW", "level": "error"})
        result = enrich_with_computed(r, "severity", lambda rec: "HIGH")
        assert result.data["severity"] == "HIGH"


class TestEnrichRecords:
    def test_applies_static_to_all(self):
        records = [make_record({"msg": str(i)}) for i in range(3)]
        result = list(enrich_records(records, static_fields={"env": "test"}))
        assert all(r.data["env"] == "test" for r in result)

    def test_applies_computed_to_all(self):
        records = [make_record({"level": "warn"}), make_record({"level": "info"})]
        fn = lambda r: r.data.get("level", "").upper()
        result = list(enrich_records(records, computed_fields={"LEVEL": fn}))
        assert result[0].data["LEVEL"] == "WARN"
        assert result[1].data["LEVEL"] == "INFO"

    def test_empty_input_yields_nothing(self):
        result = list(enrich_records([], static_fields={"env": "prod"}))
        assert result == []

    def test_no_enrichments_passes_through(self):
        records = [make_record({"msg": "hi"})]
        result = list(enrich_records(records))
        assert result[0].data["msg"] == "hi"
