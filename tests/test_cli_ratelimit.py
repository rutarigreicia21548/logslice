"""Tests for logslice.cli_ratelimit."""

import argparse
import pytest
from logslice.parser import LogRecord
from logslice.cli_ratelimit import add_ratelimit_args, apply_ratelimit


def make_record(msg: str = "hi") -> LogRecord:
    return LogRecord(raw=f'{{"message": "{msg}"}}', data={"message": msg})


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"rate_limit": None, "burst_limit": None, "burst_window": 1.0}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddRatelimitArgs:
    def setup_method(self):
        self.parser = argparse.ArgumentParser()
        add_ratelimit_args(self.parser)

    def test_rate_limit_default_is_none(self):
        args = self.parser.parse_args([])
        assert args.rate_limit is None

    def test_burst_limit_default_is_none(self):
        args = self.parser.parse_args([])
        assert args.burst_limit is None

    def test_burst_window_default_is_one(self):
        args = self.parser.parse_args([])
        assert args.burst_window == 1.0

    def test_rate_limit_parses_float(self):
        args = self.parser.parse_args(["--rate-limit", "25.5"])
        assert args.rate_limit == pytest.approx(25.5)

    def test_burst_limit_parses_int(self):
        args = self.parser.parse_args(["--burst-limit", "100"])
        assert args.burst_limit == 100

    def test_burst_window_parses_float(self):
        args = self.parser.parse_args(["--burst-window", "0.5"])
        assert args.burst_window == pytest.approx(0.5)


class TestApplyRatelimit:
    def test_no_limits_returns_all_records(self):
        records = [make_record(str(i)) for i in range(5)]
        args = _make_namespace()
        result = list(apply_ratelimit(records, args))
        assert len(result) == 5

    def test_rate_limit_applied_when_set(self):
        records = [make_record(str(i)) for i in range(3)]
        args = _make_namespace(rate_limit=1000.0)
        result = list(apply_ratelimit(records, args))
        assert len(result) == 3

    def test_burst_limit_applied_when_set(self):
        records = [make_record(str(i)) for i in range(10)]
        args = _make_namespace(burst_limit=4, burst_window=10.0)
        result = list(apply_ratelimit(records, args))
        assert len(result) == 4

    def test_both_limits_applied_together(self):
        records = [make_record(str(i)) for i in range(8)]
        args = _make_namespace(rate_limit=1000.0, burst_limit=5, burst_window=10.0)
        result = list(apply_ratelimit(records, args))
        assert len(result) == 5

    def test_returns_iterator(self):
        records = [make_record()]
        args = _make_namespace()
        result = apply_ratelimit(records, args)
        # Should be iterable but not necessarily a list
        assert hasattr(result, "__iter__")
