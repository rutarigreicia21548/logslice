# Field Enrichment — Integration Guide

The `--enrich` flag lets you attach static key-value fields to every log record
that passes through the pipeline. Fields are only added when the key is **not
already present** in the record, so source data is never silently overwritten.

## Usage

```bash
# Tag every record with an environment label
logslice --enrich env=production app.log

# Attach multiple fields
logslice --enrich env=staging --enrich region=us-east-1 app.log

# Combine with filtering and pretty output
logslice --level error --enrich env=prod --format pretty app.log
```

## Behaviour

| Situation | Result |
|---|---|
| Key absent in record | Field is added with the supplied value |
| Key already present | Record is passed through unchanged |
| Multiple `--enrich` flags | All fields are applied left-to-right |
| No `--enrich` flags | Records are passed through unchanged |

## Programmatic API

```python
from logslice.enrich import enrich_records

enriched = enrich_records(
    records,
    static_fields={"env": "prod", "region": "eu"},
    computed_fields={"level_upper": lambda r: r.data.get("level", "").upper()},
)
```

`computed_fields` accepts callables that receive the full `LogRecord` and return
a string value (or `None` to skip the field). Computed fields **do** overwrite
existing values, giving you a lightweight normalisation hook.
