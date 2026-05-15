"""Tests for logslice.cli_enrich."""

import argparse
import pytest
from logslice.parser import LogRecord
from logslice.cli_enrich import add_enrich_args, _parse_enrich_arg, apply_enrichment


def make_record(data=None, raw="{}"):
    return LogRecord(data=data or {}, raw=raw, parse_error=None)


def _make_namespace(**kwargs):
    ns = argparse.Namespace()
    ns.enrich = kwargs.get("enrich", [])
    return ns


class TestAddEnrichArgs:
    def setup_method(self):
        self.parser = argparse.ArgumentParser()
        add_enrich_args(self.parser)

    def test_default_is_empty_list(self):
        args = self.parser.parse_args([])
        assert args.enrich == []

    def test_single_enrich_arg(self):
        args = self.parser.parse_args(["--enrich", "env=prod"])
        assert args.enrich == ["env=prod"]

    def test_multiple_enrich_args(self):
        args = self.parser.parse_args(["--enrich", "env=prod", "--enrich", "region=us"])
        assert args.enrich == ["env=prod", "region=us"]


class TestParseEnrichArg:
    def test_valid_key_value(self):
        key, value = _parse_enrich_arg("env=production")
        assert key == "env"
        assert value == "production"

    def test_value_with_equals_sign(self):
        key, value = _parse_enrich_arg("url=http://x.com/a=1")
        assert key == "url"
        assert value == "http://x.com/a=1"

    def test_missing_equals_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_enrich_arg("noequals")

    def test_empty_key_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_enrich_arg("=value")


class TestApplyEnrichment:
    def test_adds_static_field(self):
        records = [make_record({"msg": "hi"})]
        args = _make_namespace(enrich=["env=prod"])
        result = list(apply_enrichment(iter(records), args))
        assert result[0].data["env"] == "prod"

    def test_no_enrich_passes_through(self):
        records = [make_record({"msg": "hi"})]
        args = _make_namespace(enrich=[])
        result = list(apply_enrichment(iter(records), args))
        assert result[0].data["msg"] == "hi"
        assert "env" not in result[0].data

    def test_multiple_fields(self):
        records = [make_record({})]
        args = _make_namespace(enrich=["env=prod", "region=eu"])
        result = list(apply_enrichment(iter(records), args))
        assert result[0].data["env"] == "prod"
        assert result[0].data["region"] == "eu"
