"""Format log records using Go-style template strings.

Templates use {field} placeholders which are replaced with values
from the parsed record. Missing fields fall back to a configurable
default string.
"""

from __future__ import annotations

import re
from typing import Iterator

from logslice.parser import LogRecord, get

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

_DEFAULT_MISSING = ""


def render_template(template: str, record: LogRecord, missing: str = _DEFAULT_MISSING) -> str:
    """Return *template* with {field} placeholders substituted from *record*.

    Unknown fields are replaced with *missing*.
    """

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        field = match.group(1)
        value = get(record, field)
        if value is None:
            return missing
        return str(value)

    return _PLACEHOLDER_RE.sub(_replace, template)


def make_template_formatter(template: str, missing: str = _DEFAULT_MISSING):
    """Return a callable that formats a single *LogRecord* using *template*."""

    def _format(record: LogRecord) -> str:
        return render_template(template, record, missing=missing)

    return _format


def template_records(
    records: Iterator[LogRecord],
    template: str,
    missing: str = _DEFAULT_MISSING,
) -> Iterator[str]:
    """Yield formatted strings for each record in *records*."""
    formatter = make_template_formatter(template, missing=missing)
    for record in records:
        yield formatter(record)
