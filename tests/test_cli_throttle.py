"""Tests for logslice.cli_throttle."""

from __future__ import annotations

import argparse
from typing import List

import pytest

from logslice.parser import LogRecord
from logslice.cli_throttle import add_throttle_args, apply_throttle


def make_record(message: str = "hello") -> LogRecord:
    return LogRecord(raw=f'{{"message": "{message}"}}', data={"message": message}, parse_error=None)


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"throttle_window": None, "throttle_max": 1, "throttle_field": "message"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddThrottleArgs:
    def setup_method(self):
        self.parser = argparse.ArgumentParser()
        add_throttle_args(self.parser)

    def test_throttle_window_default_is_none(self):
        args = self.parser.parse_args([])
        assert args.throttle_window is None

    def test_throttle_max_default_is_one(self):
        args = self.parser.parse_args([])
        assert args.throttle_max == 1

    def test_throttle_field_default_is_message(self):
        args = self.parser.parse_args([])
        assert args.throttle_field == "message"

    def test_accepts_throttle_window(self):
        args = self.parser.parse_args(["--throttle-window", "5.0"])
        assert args.throttle_window == pytest.approx(5.0)

    def test_accepts_throttle_max(self):
        args = self.parser.parse_args(["--throttle-max", "3"])
        assert args.throttle_max == 3

    def test_accepts_throttle_field(self):
        args = self.parser.parse_args(["--throttle-field", "msg"])
        assert args.throttle_field == "msg"


class TestApplyThrottle:
    def _records(self, n: int = 3) -> List[LogRecord]:
        return [make_record("hello")] * n

    def test_no_window_returns_records_unchanged(self):
        records = self._records(3)
        args = _make_namespace(throttle_window=None)
        result = list(apply_throttle(records, args))
        assert len(result) == 3

    def test_with_window_suppresses_duplicates(self):
        records = self._records(3)
        args = _make_namespace(throttle_window=60.0)
        result = list(apply_throttle(records, args))
        assert len(result) == 1

    def test_respects_max_per_window(self):
        records = self._records(5)
        args = _make_namespace(throttle_window=60.0, throttle_max=2)
        result = list(apply_throttle(records, args))
        assert len(result) == 2

    def test_respects_custom_field(self):
        records = [
            LogRecord(raw=r, data={"svc": "api", "message": m}, parse_error=None)
            for r, m in [('{"svc":"api"}', "a"), ('{"svc":"api"}', "b")]
        ]
        args = _make_namespace(throttle_window=60.0, throttle_field="svc")
        result = list(apply_throttle(records, args))
        assert len(result) == 1
