"""Tests for logslice.redact."""

import pytest
from logslice.parser import LogRecord
from logslice.redact import redact_field, redact_fields, redact_records, _REDACTED


def make_record(data: dict, raw: str = "") -> LogRecord:
    return LogRecord(raw=raw or str(data), parsed=data, source=None, parse_error=None)


class TestRedactField:
    def test_replaces_existing_field(self):
        record = make_record({"password": "secret", "user": "alice"})
        result = redact_field(record, "password")
        assert result.parsed["password"] == _REDACTED

    def test_leaves_other_fields_intact(self):
        record = make_record({"password": "secret", "user": "alice"})
        result = redact_field(record, "password")
        assert result.parsed["user"] == "alice"

    def test_missing_field_returns_original(self):
        record = make_record({"user": "alice"})
        result = redact_field(record, "token")
        assert result is record

    def test_unparsed_record_returned_unchanged(self):
        record = LogRecord(raw="bad", parsed=None, source=None, parse_error="err")
        result = redact_field(record, "password")
        assert result is record

    def test_does_not_mutate_original(self):
        original = {"password": "secret"}
        record = make_record(original)
        redact_field(record, "password")
        assert original["password"] == "secret"

    def test_preserves_raw(self):
        record = make_record({"password": "secret"}, raw="original raw")
        result = redact_field(record, "password")
        assert result.raw == "original raw"

    def test_preserves_source(self):
        record = LogRecord(
            raw="x", parsed={"token": "abc"}, source="svc-a", parse_error=None
        )
        result = redact_field(record, "token")
        assert result.source == "svc-a"


class TestRedactFields:
    def test_redacts_multiple_fields(self):
        record = make_record({"a": "1", "b": "2", "c": "3"})
        result = redact_fields(record, ["a", "b"])
        assert result.parsed["a"] == _REDACTED
        assert result.parsed["b"] == _REDACTED
        assert result.parsed["c"] == "3"

    def test_empty_field_list_returns_original(self):
        record = make_record({"a": "1"})
        result = redact_fields(record, [])
        assert result is record


class TestRedactRecords:
    def test_yields_redacted_records(self):
        records = [
            make_record({"password": "s", "msg": "hello"}),
            make_record({"password": "t", "msg": "world"}),
        ]
        results = list(redact_records(records, ["password"]))
        assert all(r.parsed["password"] == _REDACTED for r in results)

    def test_empty_fields_passes_through(self):
        records = [make_record({"password": "s"})]
        results = list(redact_records(records, []))
        assert results[0].parsed["password"] == "s"

    def test_empty_iterable_returns_nothing(self):
        results = list(redact_records([], ["password"]))
        assert results == []
