"""Tests for logslice.template."""

from __future__ import annotations

import pytest

from logslice.parser import LogRecord
from logslice.template import (
    make_template_formatter,
    render_template,
    template_records,
)


def make_record(data: dict, raw: str = "") -> LogRecord:
    return LogRecord(data=data, raw=raw or str(data))


class TestRenderTemplate:
    def test_substitutes_known_field(self):
        record = make_record({"level": "info", "msg": "hello"})
        result = render_template("{level}: {msg}", record)
        assert result == "info: hello"

    def test_missing_field_uses_empty_string_by_default(self):
        record = make_record({"level": "warn"})
        result = render_template("{level} {missing}", record)
        assert result == "warn "

    def test_missing_field_uses_custom_placeholder(self):
        record = make_record({"level": "error"})
        result = render_template("{level} {msg}", record, missing="<n/a>")
        assert result == "error <n/a>"

    def test_no_placeholders_returns_template_unchanged(self):
        record = make_record({"level": "debug"})
        result = render_template("static string", record)
        assert result == "static string"

    def test_numeric_value_converted_to_string(self):
        record = make_record({"code": 404})
        result = render_template("status={code}", record)
        assert result == "status=404"

    def test_repeated_placeholder_substituted_each_time(self):
        record = make_record({"svc": "api"})
        result = render_template("{svc}/{svc}", record)
        assert result == "api/api"

    def test_empty_template_returns_empty_string(self):
        record = make_record({"level": "info"})
        result = render_template("", record)
        assert result == ""

    def test_none_data_field_uses_missing(self):
        record = LogRecord(data={"field": None}, raw="{}")
        result = render_template("{field}", record, missing="-")
        assert result == "-"


class TestMakeTemplateFormatter:
    def test_returns_callable(self):
        formatter = make_template_formatter("{level}")
        assert callable(formatter)

    def test_formats_record(self):
        formatter = make_template_formatter("[{level}] {msg}")
        record = make_record({"level": "info", "msg": "started"})
        assert formatter(record) == "[info] started"

    def test_custom_missing_propagated(self):
        formatter = make_template_formatter("{msg}", missing="?")
        record = make_record({})
        assert formatter(record) == "?"


class TestTemplateRecords:
    def test_yields_formatted_strings(self):
        records = [
            make_record({"level": "info", "msg": "a"}),
            make_record({"level": "warn", "msg": "b"}),
        ]
        results = list(template_records(iter(records), "{level}: {msg}"))
        assert results == ["info: a", "warn: b"]

    def test_empty_input_yields_nothing(self):
        results = list(template_records(iter([]), "{level}"))
        assert results == []

    def test_missing_field_uses_default(self):
        records = [make_record({"level": "debug"})]
        results = list(template_records(iter(records), "{level}|{msg}", missing="-"))
        assert results == ["debug|-"]
