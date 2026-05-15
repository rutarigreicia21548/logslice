"""Tests for logslice.cli_mask."""

import argparse
import json
import pytest

from logslice.parser import LogRecord
from logslice.cli_mask import add_mask_args, apply_masking


def make_record(data: dict) -> LogRecord:
    raw = json.dumps(data)
    return LogRecord(raw=raw, data=data, parse_error=None)


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "mask_fields": [],
        "mask_pattern": None,
        "mask_replacement": "***",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddMaskArgs:
    def setup_method(self):
        self.parser = argparse.ArgumentParser()
        add_mask_args(self.parser)

    def test_default_fields_is_empty_list(self):
        args = self.parser.parse_args([])
        assert args.mask_fields == []

    def test_default_pattern_is_none(self):
        args = self.parser.parse_args([])
        assert args.mask_pattern is None

    def test_default_replacement_is_stars(self):
        args = self.parser.parse_args([])
        assert args.mask_replacement == "***"

    def test_accepts_mask_field(self):
        args = self.parser.parse_args(["--mask-field", "email"])
        assert "email" in args.mask_fields

    def test_accepts_multiple_mask_fields(self):
        args = self.parser.parse_args(["--mask-field", "email", "--mask-field", "ip"])
        assert args.mask_fields == ["email", "ip"]

    def test_accepts_mask_pattern(self):
        args = self.parser.parse_args(["--mask-pattern", "email"])
        assert args.mask_pattern == "email"

    def test_accepts_custom_replacement(self):
        args = self.parser.parse_args(["--mask-replacement", "[X]"])
        assert args.mask_replacement == "[X]"


class TestApplyMasking:
    def test_no_fields_returns_records_unchanged(self):
        record = make_record({"email": "a@b.com"})
        args = _make_namespace(mask_fields=[], mask_pattern="email")
        result = list(apply_masking(iter([record]), args))
        assert result[0].data["email"] == "a@b.com"

    def test_no_pattern_returns_records_unchanged(self):
        record = make_record({"email": "a@b.com"})
        args = _make_namespace(mask_fields=["email"], mask_pattern=None)
        result = list(apply_masking(iter([record]), args))
        assert result[0].data["email"] == "a@b.com"

    def test_masks_field_when_both_provided(self):
        record = make_record({"email": "user@example.com"})
        args = _make_namespace(mask_fields=["email"], mask_pattern="email")
        result = list(apply_masking(iter([record]), args))
        assert result[0].data["email"] == "***"

    def test_uses_custom_replacement(self):
        record = make_record({"ip": "10.0.0.1"})
        args = _make_namespace(
            mask_fields=["ip"], mask_pattern="ipv4", mask_replacement="[IP]"
        )
        result = list(apply_masking(iter([record]), args))
        assert result[0].data["ip"] == "[IP]"
