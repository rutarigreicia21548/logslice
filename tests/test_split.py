"""Tests for logslice.split."""

from __future__ import annotations

import os

import pytest

from logslice.parser import LogRecord
from logslice.split import (
    make_output_path,
    split_by_field,
    split_records,
    write_split,
)


def make_record(data: dict, raw: str = "") -> LogRecord:
    return LogRecord(data=data, raw=raw or str(data), parse_error=None)


# ---------------------------------------------------------------------------
# split_by_field
# ---------------------------------------------------------------------------

class TestSplitByField:
    def test_groups_by_field_value(self):
        records = [
            make_record({"service": "api"}),
            make_record({"service": "worker"}),
            make_record({"service": "api"}),
        ]
        buckets = split_by_field(records, "service")
        assert len(buckets["api"]) == 2
        assert len(buckets["worker"]) == 1

    def test_missing_field_uses_placeholder(self):
        records = [make_record({"level": "info"})]
        buckets = split_by_field(records, "service", placeholder="_none")
        assert "_none" in buckets

    def test_empty_iterable_returns_empty_dict(self):
        assert split_by_field([], "service") == {}

    def test_single_bucket(self):
        records = [make_record({"env": "prod"}) for _ in range(3)]
        buckets = split_by_field(records, "env")
        assert list(buckets.keys()) == ["prod"]
        assert len(buckets["prod"]) == 3


# ---------------------------------------------------------------------------
# split_records
# ---------------------------------------------------------------------------

class TestSplitRecords:
    def test_yields_key_record_pairs(self):
        records = [make_record({"svc": "a"}), make_record({"svc": "b"})]
        pairs = list(split_records(records, "svc"))
        assert pairs[0][0] == "a"
        assert pairs[1][0] == "b"

    def test_missing_field_yields_placeholder(self):
        records = [make_record({})]
        pairs = list(split_records(records, "svc", placeholder="X"))
        assert pairs[0][0] == "X"


# ---------------------------------------------------------------------------
# make_output_path
# ---------------------------------------------------------------------------

class TestMakeOutputPath:
    def test_builds_path(self):
        path = make_output_path("/tmp/logs", "api")
        assert path == "/tmp/logs/api.log"

    def test_sanitises_special_chars(self):
        path = make_output_path("/out", "my/service:v2")
        assert "/" not in os.path.basename(path)
        assert ":" not in os.path.basename(path)

    def test_custom_extension(self):
        path = make_output_path("/out", "svc", extension=".jsonl")
        assert path.endswith(".jsonl")


# ---------------------------------------------------------------------------
# write_split
# ---------------------------------------------------------------------------

class TestWriteSplit:
    def test_creates_files(self, tmp_path):
        records = [
            make_record({"svc": "a"}, raw='{"svc":"a"}'),
            make_record({"svc": "b"}, raw='{"svc":"b"}'),
        ]
        counts = write_split(records, "svc", str(tmp_path))
        assert counts == {"a": 1, "b": 1}
        assert (tmp_path / "a.log").exists()
        assert (tmp_path / "b.log").exists()

    def test_returns_correct_counts(self, tmp_path):
        records = [make_record({"svc": "x"}, raw="{}") for _ in range(4)]
        counts = write_split(records, "svc", str(tmp_path))
        assert counts["x"] == 4

    def test_creates_directory_if_missing(self, tmp_path):
        out = str(tmp_path / "new" / "dir")
        write_split([], "svc", out)
        assert os.path.isdir(out)
