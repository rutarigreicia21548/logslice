"""JSON log line parser for logslice."""

import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LogRecord:
    """Represents a single parsed log record."""

    raw: str
    data: dict[str, Any] = field(default_factory=dict)
    parse_error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.parse_error is None

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a field from the parsed log data."""
        return self.data.get(key, default)

    def matches(self, filters: dict[str, Any]) -> bool:
        """
        Return True if all key/value pairs in filters match the log record.
        String comparisons are case-insensitive substring matches.
        """
        for key, expected in filters.items():
            actual = self.data.get(key)
            if actual is None:
                return False
            if isinstance(expected, str) and isinstance(actual, str):
                if expected.lower() not in actual.lower():
                    return False
            else:
                if actual != expected:
                    return False
        return True


def parse_line(line: str) -> LogRecord:
    """
    Parse a single log line as JSON.

    Returns a LogRecord with parse_error set if the line is not valid JSON
    or does not parse to a dict.
    """
    stripped = line.rstrip("\n")
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return LogRecord(raw=stripped, parse_error=str(exc))

    if not isinstance(data, dict):
        return LogRecord(
            raw=stripped,
            parse_error=f"Expected JSON object, got {type(data).__name__}",
        )

    return LogRecord(raw=stripped, data=data)
