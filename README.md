# logslice

> Stream and filter structured JSON logs from multiple services with a single command.

---

## Installation

```bash
pip install logslice
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install logslice
```

---

## Usage

Stream logs from one or more services and filter by field values:

```bash
# Stream logs from a single service
logslice stream --service api

# Stream from multiple services and filter by log level
logslice stream --service api --service worker --filter level=error

# Filter by a nested field and pretty-print output
logslice stream --service api --filter status=500 --pretty

# Read from a local JSON log file
logslice slice app.log --filter user_id=42
```

### Example output

```
[api]     2024-03-12T10:22:01Z  ERROR  "database connection timeout"  host=db-1
[worker]  2024-03-12T10:22:03Z  ERROR  "job failed after 3 retries"   job_id=8821
```

---

## Configuration

Place a `logslice.toml` in your project root to define services and default filters:

```toml
[services]
api    = "http://localhost:4000/logs"
worker = "http://localhost:4001/logs"

[defaults]
pretty = true
```

---

## License

MIT © [logslice contributors](LICENSE)