"""Tests for logslice.highlight."""

import pytest

from logslice.highlight import (
    ANSI_RESET,
    ANSI_COLORS,
    colorize,
    level_color,
    highlight_level,
    highlight_field,
)


class TestColorize:
    def test_wraps_text_with_ansi_codes(self):
        result = colorize("hello", "red", enabled=True)
        assert result == f"{ANSI_COLORS['red']}hello{ANSI_RESET}"

    def test_disabled_returns_plain_text(self):
        result = colorize("hello", "red", enabled=False)
        assert result == "hello"

    def test_unknown_color_returns_plain_text(self):
        result = colorize("hello", "ultraviolet", enabled=True)
        assert result == "hello"

    def test_bold(self):
        result = colorize("msg", "bold", enabled=True)
        assert ANSI_COLORS["bold"] in result
        assert ANSI_RESET in result


class TestLevelColor:
    def test_error_is_red(self):
        assert level_color("error") == "red"

    def test_warn_is_yellow(self):
        assert level_color("warn") == "yellow"

    def test_warning_is_yellow(self):
        assert level_color("warning") == "yellow"

    def test_info_is_green(self):
        assert level_color("info") == "green"

    def test_debug_is_dim(self):
        assert level_color("debug") == "dim"

    def test_unknown_level_defaults_to_white(self):
        assert level_color("verbose") == "white"

    def test_case_insensitive(self):
        assert level_color("ERROR") == "red"
        assert level_color("Info") == "green"


class TestHighlightLevel:
    def test_uppercases_level(self):
        result = highlight_level("info", enabled=False)
        assert result == "INFO"

    def test_contains_color_code_when_enabled(self):
        result = highlight_level("error", enabled=True)
        assert ANSI_COLORS["red"] in result
        assert "ERROR" in result

    def test_no_color_codes_when_disabled(self):
        result = highlight_level("error", enabled=False)
        assert "\033[" not in result


class TestHighlightField:
    def test_formats_key_value(self):
        result = highlight_field("service", "api", enabled=False)
        assert result == "service=api"

    def test_key_is_cyan_when_enabled(self):
        result = highlight_field("service", "api", enabled=True)
        assert ANSI_COLORS["cyan"] in result
        assert "service" in result
        assert "=api" in result

    def test_no_codes_when_disabled(self):
        result = highlight_field("k", "v", enabled=False)
        assert "\033[" not in result
