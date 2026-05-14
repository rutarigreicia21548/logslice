"""Terminal color/highlight utilities for logslice output."""

from __future__ import annotations

ANSI_RESET = "\033[0m"

ANSI_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}

LEVEL_COLORS = {
    "error": "red",
    "fatal": "red",
    "critical": "red",
    "warn": "yellow",
    "warning": "yellow",
    "info": "green",
    "debug": "dim",
    "trace": "dim",
}


def colorize(text: str, color: str, enabled: bool = True) -> str:
    """Wrap *text* in ANSI escape codes for *color*.

    If *enabled* is False the text is returned unchanged.
    """
    if not enabled:
        return text
    code = ANSI_COLORS.get(color)
    if code is None:
        return text
    return f"{code}{text}{ANSI_RESET}"


def level_color(level: str) -> str:
    """Return the color name associated with *level*, defaulting to 'white'."""
    return LEVEL_COLORS.get(level.lower(), "white")


def highlight_level(level: str, enabled: bool = True) -> str:
    """Return *level* string wrapped in its associated color."""
    color = level_color(level)
    return colorize(level.upper(), color, enabled=enabled)


def highlight_field(key: str, value: str, enabled: bool = True) -> str:
    """Return a formatted key=value pair with the key highlighted in cyan."""
    colored_key = colorize(key, "cyan", enabled=enabled)
    return f"{colored_key}={value}"
