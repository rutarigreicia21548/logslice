"""Tests for logslice.dedup."""

from __future__ import annotations

import json
import pytest

from logslice.parser import LogRecord
from logslice.dedup import dedup_records, _fingerprint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_record(data: dict | None = None, raw: str = "") -> LogRecord:
    if data is None:
        data = {}
    if not raw:
        raw = json.dumps(data)
    return LogRecord(raw=raw, data=data, parse_error=None)


# ---------------------------------------------------------------------------
# _fingerprint
# ---------------------------------------------------------------------------

class TestFingerprint:
    def test_uses_field_when_present(self):
        rec = make_record({"msg": "hello", "level": "info"})
        assert _fingerprint(rec, field="msg") == "hello"

    def test_falls_back_to_raw_when_field_missing(self):
        rec = make_record({"level": "info"}, raw="raw line")
        assert _fingerprint(rec, field="msg") == "raw line"

    def test_no_field_uses_raw(self):
        rec = make_record({"msg": "hi"}, raw="  raw  ")
        assert _fingerprint(rec) == "raw"

    def test_field_none_falls_back_to_raw(self):
        rec = make_record({}, raw="plain")
        assert _fingerprint(rec, field=None) == "plain"


# ---------------------------------------------------------------------------
# dedup_records
# ---------------------------------------------------------------------------

class TestDedupRecords:
    def test_passes_unique_records_through(self):
        records = [
            make_record({"msg": "a"}, raw="a"),
            make_record({"msg": "b"}, raw="b"),
            make_record({"msg": "c"}, raw="c"),
        ]
        result = list(dedup_records(records))
        assert len(result) == 3

    def test_drops_exact_duplicate_raw(self):
        records = [
            make_record(raw="dup line"),
            make_record(raw="dup line"),
            make_record(raw="unique"),
        ]
        result = list(dedup_records(records))
        assert len(result) == 2
        assert result[0].raw == "dup line"
        assert result[1].raw == "unique"

    def test_dedup_by_field(self):
        records = [
            make_record({"msg": "same"}),
            make_record({"msg": "same"}),
            make_record({"msg": "different"}),
        ]
        result = list(dedup_records(records, field="msg"))
        assert len(result) == 2

    def test_window_evicts_old_fingerprints(self):
        # With window=1, the first record should be re-admitted after the
        # second record evicts it from the seen set.
        r_a1 = make_record(raw="a")
        r_b = make_record(raw="b")
        r_a2 = make_record(raw="a")
        result = list(dedup_records([r_a1, r_b, r_a2], window=1))
        assert len(result) == 3

    def test_empty_iterable_returns_nothing(self):
        assert list(dedup_records([])) == []

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window must be >= 1"):
            list(dedup_records([], window=0))
