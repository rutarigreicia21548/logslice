"""Tests for logslice.cli_split."""

from __future__ import annotations

import argparse
import os

import pytest

from logslice.cli_split import add_split_args, apply_split
from logslice.parser import LogRecord


def make_record(data: dict, raw: str = "") -> LogRecord:
    return LogRecord(data=data, raw=raw or str(data), parse_error=None)


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "split_by": None,
        "split_dir": "split_output",
        "split_placeholder": "_unknown",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddSplitArgs:
    def setup_method(self):
        self.parser = argparse.ArgumentParser()
        add_split_args(self.parser)

    def test_default_split_by_is_none(self):
        args = self.parser.parse_args([])
        assert args.split_by is None

    def test_accepts_split_by_flag(self):
        args = self.parser.parse_args(["--split-by", "service"])
        assert args.split_by == "service"

    def test_default_split_dir(self):
        args = self.parser.parse_args([])
        assert args.split_dir == "split_output"

    def test_accepts_split_dir(self):
        args = self.parser.parse_args(["--split-dir", "/tmp/out"])
        assert args.split_dir == "/tmp/out"

    def test_default_placeholder(self):
        args = self.parser.parse_args([])
        assert args.split_placeholder == "_unknown"


class TestApplySplit:
    def test_passthrough_when_no_split_by(self):
        records = [make_record({"svc": "a"}), make_record({"svc": "b"})]
        args = _make_namespace(split_by=None)
        result = list(apply_split(iter(records), args))
        assert len(result) == 2

    def test_yields_all_records_when_split_active(self, tmp_path):
        records = [
            make_record({"svc": "a"}, raw='{"svc":"a"}'),
            make_record({"svc": "b"}, raw='{"svc":"b"}'),
            make_record({"svc": "a"}, raw='{"svc":"a"}'),
        ]
        args = _make_namespace(split_by="svc", split_dir=str(tmp_path))
        result = list(apply_split(iter(records), args))
        assert len(result) == 3

    def test_writes_files_by_field(self, tmp_path):
        records = [
            make_record({"env": "prod"}, raw='{"env":"prod"}'),
            make_record({"env": "dev"}, raw='{"env":"dev"}'),
        ]
        args = _make_namespace(split_by="env", split_dir=str(tmp_path))
        list(apply_split(iter(records), args))
        assert (tmp_path / "prod.log").exists()
        assert (tmp_path / "dev.log").exists()

    def test_missing_field_uses_placeholder(self, tmp_path):
        records = [make_record({}, raw="{}")]
        args = _make_namespace(
            split_by="env",
            split_dir=str(tmp_path),
            split_placeholder="_none",
        )
        list(apply_split(iter(records), args))
        assert (tmp_path / "_none.log").exists()
