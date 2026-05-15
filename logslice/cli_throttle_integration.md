# Throttle Integration Guide

The `--throttle-window` flag suppresses repeated log records that share the
same message (or any chosen field) within a rolling time window.

## CLI Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--throttle-window SECONDS` | float | `None` (disabled) | Rolling window size in seconds |
| `--throttle-max N` | int | `1` | Max occurrences allowed per window |
| `--throttle-field FIELD` | str | `message` | Field used to identify duplicates |

## Examples

### Suppress duplicate error messages seen more than once per 10 seconds

```bash
tail -f app.log | logslice --throttle-window 10
```

### Allow up to 3 occurrences of the same message per minute

```bash
logslice service.log --throttle-window 60 --throttle-max 3
```

### Throttle by service name instead of message text

```bash
logslice service.log --throttle-window 5 --throttle-field service
```

## Programmatic Usage

```python
from logslice.throttle import throttle_records

filtered = throttle_records(records, window=30, field="message", max_per_window=1)
for record in filtered:
    print(record.raw)
```

## Integration in `cli.py`

Add the following calls inside `build_arg_parser` and `run`:

```python
# build_arg_parser
from logslice.cli_throttle import add_throttle_args
add_throttle_args(parser)

# run — after other record transformations
from logslice.cli_throttle import apply_throttle
records = apply_throttle(records, args)
```
