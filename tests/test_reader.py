"""Tests for logslice.reader."""

import io
import json
import sys
import tempfile
import os
import pytest
from unittest.mock import patch
from logslice.reader import stream_lines, stream_records, _iter_lines


def write_tmp(lines):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    f.writelines(lines)
    f.flush()
    f.close()
    return f.name


class TestStreamLines:
    def test_reads_valid_json_lines(self):
        path = write_tmp(['{"msg": "a"}\n', '{"msg": "b"}\n'])
        try:
            records = list(stream_lines([path]))
            assert len(records) == 2
            assert records[0].data["msg"] == "a"
        finally:
            os.unlink(path)

    def test_injects_source_label(self):
        path = write_tmp(['{"msg": "hi"}\n'])
        try:
            records = list(stream_lines([path]))
            assert records[0].data["_source"] == path
        finally:
            os.unlink(path)

    def test_does_not_overwrite_existing_source(self):
        path = write_tmp(['{"msg": "hi", "_source": "custom"}\n'])
        try:
            records = list(stream_lines([path]))
            assert records[0].data["_source"] == "custom"
        finally:
            os.unlink(path)

    def test_missing_file_yields_error_record(self):
        records = list(stream_lines(["/nonexistent/path.log"]))
        assert len(records) == 1
        assert records[0].parse_error is not None

    def test_reads_from_stdin(self):
        fake_stdin = io.StringIO('{"msg": "stdin"}\n')
        with patch("logslice.reader.sys.stdin", fake_stdin):
            records = list(stream_lines(["-"]))
        assert records[0].data["msg"] == "stdin"

    def test_multiple_sources(self):
        p1 = write_tmp(['{"msg": "x"}\n'])
        p2 = write_tmp(['{"msg": "y"}\n'])
        try:
            records = list(stream_lines([p1, p2]))
            assert len(records) == 2
        finally:
            os.unlink(p1)
            os.unlink(p2)


class TestStreamRecords:
    def test_no_predicate_yields_all(self):
        path = write_tmp(['{"level": "info"}\n', '{"level": "error"}\n'])
        try:
            records = list(stream_records([path]))
            assert len(records) == 2
        finally:
            os.unlink(path)

    def test_predicate_filters_records(self):
        path = write_tmp(['{"level": "info"}\n', '{"level": "error"}\n'])
        try:
            records = list(
                stream_records([path], predicate=lambda r: r.data.get("level") == "error")
            )
            assert len(records) == 1
            assert records[0].data["level"] == "error"
        finally:
            os.unlink(path)
