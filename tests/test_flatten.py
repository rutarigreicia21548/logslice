"""Tests for logslice.flatten and logslice.cli_flatten."""

import argparse
import pytest

from logslice.parser import LogRecord
from logslice.flatten import flatten_dict, flatten_record, flatten_records
from logslice.cli_flatten import add_flatten_args, apply_flatten


def make_record(data: dict, raw: str = "{}") -> LogRecord:
    return LogRecord(raw=raw, data=data)


# ---------------------------------------------------------------------------
# flatten_dict
# ---------------------------------------------------------------------------

class TestFlattenDict:
    def test_flat_dict_unchanged(self):
        data = {"level": "info", "msg": "hello"}
        assert flatten_dict(data) == data

    def test_nested_one_level(self):
        data = {"context": {"service": "api", "version": "1"}}
        result = flatten_dict(data)
        assert result == {"context.service": "api", "context.version": "1"}

    def test_nested_two_levels(self):
        data = {"a": {"b": {"c": 42}}}
        assert flatten_dict(data) == {"a.b.c": 42}

    def test_custom_separator(self):
        data = {"a": {"b": 1}}
        assert flatten_dict(data, sep="/") == {"a/b": 1}

    def test_mixed_nested_and_flat(self):
        data = {"level": "warn", "meta": {"host": "srv1"}}
        result = flatten_dict(data)
        assert result == {"level": "warn", "meta.host": "srv1"}

    def test_empty_dict(self):
        assert flatten_dict({}) == {}

    def test_non_dict_values_preserved(self):
        data = {"tags": ["a", "b"], "count": 3}
        assert flatten_dict(data) == data


# ---------------------------------------------------------------------------
# flatten_record
# ---------------------------------------------------------------------------

class TestFlattenRecord:
    def test_flattens_nested_data(self):
        record = make_record({"meta": {"host": "srv1"}}, raw='{"meta":{"host":"srv1"}}')
        result = flatten_record(record)
        assert result.data == {"meta.host": "srv1"}

    def test_preserves_raw_line(self):
        raw = '{"a":{"b":1}}'
        record = make_record({"a": {"b": 1}}, raw=raw)
        assert flatten_record(record).raw == raw

    def test_parse_error_record_returned_as_is(self):
        record = LogRecord(raw="not json", data={"_parse_error": "invalid"})
        assert flatten_record(record) is record

    def test_custom_sep(self):
        record = make_record({"a": {"b": 2}})
        result = flatten_record(record, sep="_")
        assert "a_b" in result.data


# ---------------------------------------------------------------------------
# flatten_records (iterator)
# ---------------------------------------------------------------------------

class TestFlattenRecords:
    def test_yields_all_records(self):
        records = [make_record({"x": {"y": 1}}), make_record({"z": 2})]
        result = list(flatten_records(iter(records)))
        assert len(result) == 2

    def test_empty_iterator(self):
        assert list(flatten_records(iter([]))) == []


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"flatten": False, "flatten_sep": "."}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddFlattenArgs:
    def setup_method(self):
        self.parser = argparse.ArgumentParser()
        add_flatten_args(self.parser)

    def test_default_flatten_is_false(self):
        args = self.parser.parse_args([])
        assert args.flatten is False

    def test_flatten_flag_sets_true(self):
        args = self.parser.parse_args(["--flatten"])
        assert args.flatten is True

    def test_default_sep_is_dot(self):
        args = self.parser.parse_args([])
        assert args.flatten_sep == "."

    def test_custom_sep(self):
        args = self.parser.parse_args(["--flatten-sep", "_"])
        assert args.flatten_sep == "_"


class TestApplyFlatten:
    def test_no_flatten_returns_original_stream(self):
        records = [make_record({"a": {"b": 1}})]
        args = _make_namespace(flatten=False)
        result = list(apply_flatten(iter(records), args))
        assert result[0].data == {"a": {"b": 1}}

    def test_flatten_true_flattens_records(self):
        records = [make_record({"a": {"b": 1}})]
        args = _make_namespace(flatten=True)
        result = list(apply_flatten(iter(records), args))
        assert result[0].data == {"a.b": 1}

    def test_flatten_with_custom_sep(self):
        records = [make_record({"a": {"b": 1}})]
        args = _make_namespace(flatten=True, flatten_sep="/")
        result = list(apply_flatten(iter(records), args))
        assert "a/b" in result[0].data
