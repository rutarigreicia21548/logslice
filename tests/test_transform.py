"""Tests for logslice.transform and logslice.cli_transform."""

import argparse
import pytest
from logslice.parser import LogRecord
from logslice.transform import rename_field, add_field, drop_field, transform_records
from logslice.cli_transform import (
    add_transform_args,
    apply_transforms,
    _parse_rename,
    _parse_add_field,
)


def make_record(data: dict) -> LogRecord:
    return LogRecord(raw="{}", data=data, parse_error=None)


class TestRenameField:
    def test_renames_existing_field(self):
        r = make_record({"old": "value", "x": 1})
        out = rename_field(r, "old", "new")
        assert "new" in out.data
        assert "old" not in out.data
        assert out.data["new"] == "value"

    def test_preserves_other_fields(self):
        r = make_record({"a": 1, "b": 2})
        out = rename_field(r, "a", "c")
        assert out.data["b"] == 2

    def test_missing_field_returns_original(self):
        r = make_record({"x": 1})
        out = rename_field(r, "missing", "new")
        assert out.data == {"x": 1}

    def test_does_not_mutate_original(self):
        r = make_record({"a": 1})
        rename_field(r, "a", "b")
        assert "a" in r.data


class TestAddField:
    def test_adds_new_field(self):
        r = make_record({"x": 1})
        out = add_field(r, "env", "prod")
        assert out.data["env"] == "prod"
        assert out.data["x"] == 1

    def test_overwrites_existing_field(self):
        r = make_record({"level": "info"})
        out = add_field(r, "level", "warn")
        assert out.data["level"] == "warn"

    def test_does_not_mutate_original(self):
        r = make_record({"a": 1})
        add_field(r, "b", 2)
        assert "b" not in r.data


class TestDropField:
    def test_removes_field(self):
        r = make_record({"secret": "abc", "msg": "hi"})
        out = drop_field(r, "secret")
        assert "secret" not in out.data
        assert out.data["msg"] == "hi"

    def test_missing_field_is_noop(self):
        r = make_record({"a": 1})
        out = drop_field(r, "ghost")
        assert out.data == {"a": 1}


class TestTransformRecords:
    def test_applies_multiple_transforms(self):
        records = [make_record({"old": "v", "drop_me": True})]
        fns = [
            lambda r: rename_field(r, "old", "new"),
            lambda r: drop_field(r, "drop_me"),
        ]
        results = list(transform_records(records, fns))
        assert results[0].data == {"new": "v"}

    def test_empty_records(self):
        assert list(transform_records([], [lambda r: r])) == []


class TestCliTransform:
    def _make_ns(self, rename=None, add_field=None, drop_field=None):
        ns = argparse.Namespace(
            rename=rename or [],
            add_field=add_field or [],
            drop_field=drop_field or [],
        )
        return ns

    def test_parse_rename_valid(self):
        assert _parse_rename("src:dst") == ("src", "dst")

    def test_parse_rename_invalid(self):
        with pytest.raises(ValueError):
            _parse_rename("nodivider")

    def test_parse_add_field_valid(self):
        assert _parse_add_field("env=prod") == ("env", "prod")

    def test_parse_add_field_invalid(self):
        with pytest.raises(ValueError):
            _parse_add_field("noequalssign")

    def test_apply_transforms_rename(self):
        ns = self._make_ns(rename=["old:new"])
        records = [make_record({"old": "val"})]
        result = list(apply_transforms(ns, records))
        assert "new" in result[0].data

    def test_apply_transforms_no_ops_returns_original(self):
        ns = self._make_ns()
        records = [make_record({"a": 1})]
        result = list(apply_transforms(ns, records))
        assert result[0].data == {"a": 1}

    def test_add_transform_args_registers_options(self):
        parser = argparse.ArgumentParser()
        add_transform_args(parser)
        args = parser.parse_args([
            "--rename", "a:b",
            "--add-field", "x=1",
            "--drop-field", "secret",
        ])
        assert args.rename == ["a:b"]
        assert args.add_field == ["x=1"]
        assert args.drop_field == ["secret"]
