# Checkpoint Integration Guide

The checkpoint feature lets `logslice` remember where it left off in each log
file so that re-running the command only processes **new** lines.

## Usage

```bash
logslice --checkpoint /var/run/logslice.json /var/log/app/*.log
```

On the first run the checkpoint file is created automatically.  Subsequent runs
read the stored byte offsets and seek each source file to that position before
yielding records.

## How it works

1. `cli_checkpoint.load_offsets(args)` reads the checkpoint file at startup.
2. `checkpoint.get_offset(offsets, source)` returns the last known position for
   a given file path, or `None` if the source is new.
3. As records are consumed the caller calls
   `cli_checkpoint.record_position(args, offsets, source, pos)` to atomically
   write the updated offset back to disk via a `.tmp` swap.

## File format

```json
{
  "version": 1,
  "offsets": {
    "/var/log/app/api.log": 204800,
    "/var/log/app/worker.log": 81920
  }
}
```

## Caveats

- Offsets are **byte** positions, not line numbers.
- If a log file is rotated (truncated) the stored offset will exceed the new
  file size; callers should detect this and reset to `0`.
- The checkpoint file is written atomically using a `.tmp` rename to avoid
  corruption on crash.
