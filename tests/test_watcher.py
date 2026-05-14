"""Tests for logslice.watcher — high-level record watching."""

import os
import tempfile
import threading
import time
from unittest.mock import patch

import pytest

from logslice.watcher import watch_records
from logslice.parser import LogRecord


def _write_after_delay(path: str, lines: list[str], delay: float = 0.05) -> None:
    def _worker():
        time.sleep(delay)
        with open(path, "a", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")
                fh.flush()
                time.sleep(0.01)

    threading.Thread(target=_worker, daemon=True).start()


class TestWatchRecords:
    def _tmp_log(self) -> str:
        fd, path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        return path

    def test_yields_parsed_records(self):
        path = self._tmp_log()
        try:
            _write_after_delay(path, ['{"level": "info", "msg": "boot"}'])
            records = []
            for rec in watch_records([path], poll_interval=0.05):
                records.append(rec)
                if len(records) >= 1:
                    break
            assert isinstance(records[0], LogRecord)
            assert records[0].data["msg"] == "boot"
        finally:
            os.unlink(path)

    def test_injects_source_label(self):
        path = self._tmp_log()
        try:
            _write_after_delay(path, ['{"msg": "hi"}'])
            for rec in watch_records([path], poll_interval=0.05):
                assert rec.data["source"] == path
                break
        finally:
            os.unlink(path)

    def test_does_not_overwrite_existing_source(self):
        path = self._tmp_log()
        try:
            _write_after_delay(path, ['{"msg": "hi", "source": "myapp"}'])
            for rec in watch_records([path], poll_interval=0.05):
                assert rec.data["source"] == "myapp"
                break
        finally:
            os.unlink(path)

    def test_predicate_filters_records(self):
        path = self._tmp_log()
        try:
            _write_after_delay(
                path,
                ['{"level": "debug", "msg": "skip"}', '{"level": "error", "msg": "keep"}'],
            )
            only_errors = lambda r: r.data is not None and r.data.get("level") == "error"
            for rec in watch_records([path], predicate=only_errors, poll_interval=0.05):
                assert rec.data["msg"] == "keep"
                break
        finally:
            os.unlink(path)
