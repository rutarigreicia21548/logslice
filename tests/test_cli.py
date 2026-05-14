"""Tests for the CLI argument parser and field argument parsing."""

import pytest
from unittest.mock import patch, MagicMock
from logslice.cli import build_arg_parser, parse_field_arg


class TestBuildArgParser:
    """Tests for build_arg_parser."""

    def setup_method(self):
        self.parser = build_arg_parser()

    def test_returns_arg_parser(self):
        import argparse
        assert isinstance(self.parser, argparse.ArgumentParser)

    def test_default_format_is_pretty(self):
        args = self.parser.parse_args([])
        assert args.format == "pretty"

    def test_format_json_option(self):
        args = self.parser.parse_args(["--format", "json"])
        assert args.format == "json"

    def test_level_filter_default_is_none(self):
        args = self.parser.parse_args([])
        assert args.level is None

    def test_level_filter_set(self):
        args = self.parser.parse_args(["--level", "error"])
        assert args.level == "error"

    def test_service_filter_default_is_none(self):
        args = self.parser.parse_args([])
        assert args.service is None

    def test_service_filter_set(self):
        args = self.parser.parse_args(["--service", "auth"])
        assert args.service == "auth"

    def test_field_filter_default_is_empty_list(self):
        args = self.parser.parse_args([])
        assert args.field == []

    def test_field_filter_single_value(self):
        args = self.parser.parse_args(["--field", "env=prod"])
        assert args.field == ["env=prod"]

    def test_field_filter_multiple_values(self):
        args = self.parser.parse_args(["--field", "env=prod", "--field", "region=us"])
        assert args.field == ["env=prod", "region=us"]

    def test_sources_default_is_empty_list(self):
        args = self.parser.parse_args([])
        assert args.sources == []

    def test_sources_positional_args(self):
        args = self.parser.parse_args(["app.log", "web.log"])
        assert args.sources == ["app.log", "web.log"]

    def test_tail_flag_default_is_false(self):
        args = self.parser.parse_args([])
        assert args.tail is False

    def test_tail_flag_set(self):
        args = self.parser.parse_args(["--tail"])
        assert args.tail is True

    def test_no_color_flag_default_is_false(self):
        args = self.parser.parse_args([])
        assert args.no_color is False

    def test_no_color_flag_set(self):
        args = self.parser.parse_args(["--no-color"])
        assert args.no_color is True

    def test_dedup_flag_default_is_false(self):
        args = self.parser.parse_args([])
        assert args.dedup is False

    def test_dedup_flag_set(self):
        args = self.parser.parse_args(["--dedup"])
        assert args.dedup is True


class TestParseFieldArg:
    """Tests for parse_field_arg."""

    def test_parses_key_value_pair(self):
        key, value = parse_field_arg("env=prod")
        assert key == "env"
        assert value == "prod"

    def test_parses_key_with_value_containing_equals(self):
        key, value = parse_field_arg("msg=hello=world")
        assert key == "msg"
        assert value == "hello=world"

    def test_raises_on_missing_equals(self):
        with pytest.raises(ValueError, match="Expected 'key=value'"):
            parse_field_arg("envprod")

    def test_raises_on_empty_key(self):
        with pytest.raises(ValueError, match="Expected 'key=value'"):
            parse_field_arg("=prod")

    def test_raises_on_empty_string(self):
        with pytest.raises(ValueError):
            parse_field_arg("")
