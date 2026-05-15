"""Tests for logslice.mask."""

import pytest
from logslice.parser import LogRecord
from logslice.mask import mask_value, mask_field, mask_records


def make_record(data: dict) -> LogRecord:
    import json
    raw = json.dumps(data)
    return LogRecord(raw=raw, data=data, parse_error=None)


class TestMaskValue:
    def test_replaces_match(self):
        assert mask_value("hello world", r"world") == "hello ***"

    def test_replaces_multiple_matches(self):
        assert mask_value("a b a", r"a") == "*** b ***"

    def test_custom_replacement(self):
        assert mask_value("secret", r"secret", replacement="[REDACTED]") == "[REDACTED]"

    def test_no_match_returns_original(self):
        assert mask_value("hello", r"xyz") == "hello"

    def test_non_string_value_returned_as_is(self):
        assert mask_value(42, r"\d+") == 42

    def test_builtin_email_pattern(self):
        result = mask_value("contact user@example.com please", "email")
        assert "user@example.com" not in result
        assert "***" in result

    def test_builtin_ipv4_pattern(self):
        result = mask_value("from 192.168.1.1 ok", "ipv4")
        assert "192.168.1.1" not in result

    def test_builtin_token_pattern(self):
        result = mask_value("token=abcdefghijklmnopqrstu", "token")
        assert "abcdefghijklmnopqrstu" not in result


class TestMaskField:
    def test_masks_existing_field(self):
        record = make_record({"email": "user@example.com", "level": "info"})
        result = mask_field(record, "email", "email")
        assert result.data["email"] == "***"

    def test_preserves_other_fields(self):
        record = make_record({"email": "user@example.com", "level": "info"})
        result = mask_field(record, "email", "email")
        assert result.data["level"] == "info"

    def test_missing_field_returns_original(self):
        record = make_record({"level": "info"})
        result = mask_field(record, "email", "email")
        assert result is record

    def test_preserves_raw(self):
        record = make_record({"msg": "hello world"})
        result = mask_field(record, "msg", r"world")
        assert result.raw == record.raw

    def test_does_not_mutate_original(self):
        record = make_record({"msg": "secret info"})
        mask_field(record, "msg", r"secret")
        assert record.data["msg"] == "secret info"


class TestMaskRecords:
    def test_masks_multiple_fields(self):
        record = make_record({"email": "a@b.com", "ip": "1.2.3.4", "level": "info"})
        results = list(mask_records([record], ["email", "ip"], r"[\w.@]+"))
        assert results[0].data["level"] == "info"
        assert results[0].data["email"] == "***"

    def test_empty_fields_list_yields_unchanged(self):
        record = make_record({"msg": "hello"})
        results = list(mask_records([record], [], r"hello"))
        assert results[0].data["msg"] == "hello"

    def test_empty_iterable_yields_nothing(self):
        results = list(mask_records([], ["msg"], r"x"))
        assert results == []
