# `--split-by` Integration Guide

The `--split-by` feature routes each log record into a separate output file
based on the value of a chosen field.  All records are still written to the
normal output stream so the rest of the pipeline is unaffected.

## CLI flags

| Flag | Default | Description |
|---|---|---|
| `--split-by FIELD` | *(disabled)* | Field whose value determines the output bucket. |
| `--split-dir DIR` | `split_output` | Directory that receives the per-bucket files. |
| `--split-placeholder LABEL` | `_unknown` | Bucket name for records missing the field. |

## Example

```bash
# Split a mixed log stream into one file per service
logslice app.log --split-by service --split-dir /var/log/split
```

This produces:

```
/var/log/split/api.log
/var/log/split/worker.log
/var/log/split/scheduler.log
```

## Programmatic usage

```python
from logslice.split import write_split, split_by_field

# Partition without writing files
buckets = split_by_field(records, field="service")
for key, bucket in buckets.items():
    print(key, len(bucket))

# Write directly to disk
counts = write_split(records, field="service", directory="/tmp/split")
print(counts)  # {"api": 42, "worker": 17}
```

## Notes

- Field values are sanitised before being used as file names; characters that
  are not alphanumeric, `-`, or `_` are replaced with `_`.
- Files are opened in **append** mode so repeated runs accumulate records.
- The output directory is created automatically if it does not exist.
