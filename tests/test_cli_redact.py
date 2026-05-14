"""Tests for logslice.cli_redact."""

import argparse
import pytest
from logslice.parser import LogRecord
from logslice.cli_redact import add_redact_args, apply_redaction
from logslice.redact import _REDACTED


def make_record(data: dict) -> LogRecord:
    return LogRecord(raw=str(data), parsed=data, source=None, parse_error=None)


def _make_namespace(**kwargs) -> argparse.Namespace:
    ns = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


class TestAddRedactArgs:
    def setup_method(self):
        self.parser = argparse.ArgumentParser()
        add_redact_args(self.parser)

    def test_default_is_empty_list(self):
        args = self.parser.parse_args([])
        assert args.redact_fields == []

    def test_single_field(self):
        args = self.parser.parse_args(["--redact", "password"])
        assert args.redact_fields == ["password"]

    def test_multiple_fields(self):
        args = self.parser.parse_args(["--redact", "password", "--redact", "token"])
        assert args.redact_fields == ["password", "token"]


class TestApplyRedaction:
    def test_redacts_specified_field(self):
        records = [make_record({"password": "secret", "msg": "hi"})]
        args = _make_namespace(redact_fields=["password"])
        results = list(apply_redaction(records, args))
        assert results[0].parsed["password"] == _REDACTED

    def test_no_fields_passes_through(self):
        records = [make_record({"password": "secret"})]
        args = _make_namespace(redact_fields=[])
        results = list(apply_redaction(records, args))
        assert results[0].parsed["password"] == "secret"

    def test_missing_attribute_defaults_to_no_redaction(self):
        records = [make_record({"password": "secret"})]
        args = _make_namespace()
        results = list(apply_redaction(records, args))
        assert results[0].parsed["password"] == "secret"

    def test_redacts_multiple_fields(self):
        records = [make_record({"a": "1", "b": "2", "c": "3"})]
        args = _make_namespace(redact_fields=["a", "b"])
        results = list(apply_redaction(records, args))
        assert results[0].parsed["a"] == _REDACTED
        assert results[0].parsed["b"] == _REDACTED
        assert results[0].parsed["c"] == "3"
