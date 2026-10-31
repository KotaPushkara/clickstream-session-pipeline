# Clickstream Event-to-Sessionization Pipeline

A beginner-friendly Python + MySQL data engineering project. It reads clickstream events from CSV, validates and quarantines bad records, deduplicates events, orders events by **event time**, assigns deterministic sessions, writes CSV outputs and optionally publishes results to MySQL.

## 1. Business rule and assumptions

- Input grain: one row per source event.
- `event_id` is the stable event key and must be globally unique.
- `user_id`, `event_type`, and `event_timestamp` are required.
- Timestamps must be ISO-8601. A timezone offset is recommended; timestamps without an offset are treated as UTC.
- Events are grouped by `user_id` and sorted by event timestamp, then `event_id` for deterministic ties.
- A new session starts only when the gap from the previous event is **greater than** `--gap-minutes` (default 30). A gap exactly equal to 30 minutes stays in the same session.
- Exact duplicate event rows are counted and skipped. If the same `event_id` appears with different content, the later conflicting row is quarantined.
- Missing/invalid required fields and malformed CSV rows are quarantined with a reason and original row number.
- Late/out-of-order events are handled when present in the same batch because processing sorts by event time. Cross-batch late-event correction is not automatic; rerun/backfill the affected input range.
- Session IDs are deterministic: `session_` plus a SHA-256 digest of `user_id` and the first event ID in the session.

## 2. Architecture

```text
CSV source
   |
   v
Ingestion (read raw rows + source_file + row number)
   |
   v
Validation + duplicate checks -------> rejects.csv
   |
   v
Event-time sorting per user
   |
   v
Sessionization (gap threshold)
   |
   v
sessions.csv + session_events.csv + run_report.json
   |
   +---- optional MySQL publishing (upsert by deterministic keys)
```

## 3. Project structure

```text
clickstream_session_pipeline/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── ingestion.py
│   ├── validation.py
│   ├── sessionization.py
│   ├── publishing.py
│   └── pipeline.py
├── tests/
│   ├── test_validation.py
│   └── test_sessionization.py
├── data/
│   ├── input/events.csv
│   ├── output/                 # generated outputs
│   └── reports/                # generated run reports
├── sql/schema.sql
├── generate_data.py
├── run_pipeline.py
├── requirements.txt
└── README.md
```

## 4. Setup (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the local CSV pipeline (no database server required):

```powershell
python run_pipeline.py --input data/input/events.csv --output-dir data/output --report-dir data/reports --gap-minutes 30
```

Generate a reproducible larger dataset:

```powershell
python generate_data.py --rows 100000 --output data/input/events_100k.csv --seed 42
```

Run it:

```powershell
python run_pipeline.py --input data/input/events_100k.csv --output-dir data/output_100k --report-dir data/reports_100k --gap-minutes 30
```

Run tests:

```powershell
pytest -q
```

## 5. MySQL setup (optional)

1. Start MySQL and create a database:
   ```sql
   CREATE DATABASE clickstream_db;
   ```
2. Apply `sql/schema.sql` to `clickstream_db`.
3. Install dependencies from `requirements.txt`.
4. Set environment variables (do not commit credentials):
   ```powershell
   $env:MYSQL_HOST="localhost"
   $env:MYSQL_PORT="3306"
   $env:MYSQL_USER="root"
   $env:MYSQL_PASSWORD="your_password"
   $env:MYSQL_DATABASE="clickstream_db"
   ```
5. Run with `--publish-mysql`:
   ```powershell
   python run_pipeline.py --input data/input/events.csv --output-dir data/output --report-dir data/reports --publish-mysql
   ```

MySQL publication uses `INSERT ... ON DUPLICATE KEY UPDATE` and deterministic primary keys, so rerunning the same output does not create duplicate target rows. The CSV outputs remain the local source of truth.

## 6. Output files

- `sessions.csv`: one row per session with start/end, event count, duration seconds and first/last event IDs.
- `session_events.csv`: one row per accepted event with its assigned session ID.
- `rejects.csv`: rejected rows with source file, row number, raw payload and reason.
- `run_report.json`: run ID, status, timestamps, input/accepted/duplicate/rejected counts, output counts, elapsed time, threshold and failure reason.

## 7. Reconciliation

For a successful run:

- `input_rows = accepted_unique_rows + exact_duplicate_rows + rejected_rows`
- `accepted_unique_rows = session_event_rows`
- `session_count = number of rows in sessions.csv`
- Sum of `event_count` in `sessions.csv` equals number of rows in `session_events.csv`.

The pipeline checks these conditions and writes them to the run report.

## 8. Idempotency, retry and backfill

- Output CSV files are overwritten for each run, not appended.
- Stable session IDs are derived from user ID and the first event ID.
- MySQL rows are upserted by primary key.
- Retry: rerun the same command after fixing infrastructure/configuration issues.
- Backfill: rerun the complete affected input file or a corrected historical extract. If a late event changes a session's first event or splits/merges sessions, regenerate the affected target output and republish it. This starter project does not delete obsolete MySQL sessions automatically; for a clean backfill, truncate target tables first or add a run-scoped replacement strategy.

## 9. Testing and performance

Tests cover normal sessions, exact threshold boundary, gap greater than threshold, out-of-order input, duplicate IDs, conflicting duplicate IDs, missing timestamps, malformed timestamps and empty input.

The generator uses a fixed random seed. A simple elapsed-time measurement is included in `run_report.json`. One reasonable next optimization for larger-than-memory inputs is partitioning by user ID and processing partitions independently, while keeping all events for a user in the same partition.

## 10. Known limitations / next steps

- Batch-oriented, in-memory processing; not a streaming/continuous event-time engine.
- No watermark-based late-event window or automatic cross-batch session repair.
- Timestamp-naive values are assumed UTC; production feeds should require explicit offsets.
- MySQL publishing is optional and needs a reachable MySQL instance.
- For production, add schema versioning, structured logging, retention policies, monitoring/alerts and transactional run publication.

## 11. Design trade-offs

This solution favors correctness and explainability over distributed infrastructure. Python's standard library keeps the core transformation lightweight and reproducible. CSV is used for easy review; MySQL is an optional analytical target. Deterministic ordering and IDs make retries predictable. Conflicting duplicate keys are rejected rather than silently choosing one version.
