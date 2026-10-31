# Clickstream Event-to-Sessionization Pipeline

## About the Project

This project is built using Python and MySQL to process clickstream data and group user activities into sessions.

It takes event data from a CSV file, checks the data for errors and duplicates, sorts events based on their timestamps, and groups them into sessions based on user activity.

The processed data is saved into CSV files. It can also be stored in a MySQL database when needed.

## 1. How Sessionization Works

The project follows a few rules while processing events:

- Each row in the input CSV represents one user event.
- Every event must have a unique `event_id`.
- The required fields are `event_id`, `user_id`, `event_type`, and `event_timestamp`.
- Timestamps should follow the ISO-8601 format. If a timestamp has no timezone information, it is treated as UTC.
- Events are grouped by user and arranged in chronological order.
- A new session starts when the time gap between two consecutive events is greater than 30 minutes.
- If the gap is exactly 30 minutes, both events remain in the same session.
- Exact duplicate records are skipped and counted.
- If the same event ID appears with different data, the conflicting record is rejected.
- Records with missing or invalid values are moved to a separate rejection file.
- Events received out of order are handled by sorting them before sessionization.

Each session gets a unique and repeatable ID generated using the user's ID and the first event ID in that session.

## 2. Project Workflow

The pipeline processes the data in the following order:

```text
CSV Input
    |
    v
Read and Ingest Events
    |
    v
Validate Records
    |
    v
Remove Duplicates
    |
    v
Sort Events by Timestamp
    |
    v
Create User Sessions
    |
    v
Generate CSV Reports
    |
    v
Optional MySQL Publishing
```

Invalid records are saved separately in `rejects.csv`.

## 3. Project Structure

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
│   ├── input/
│   │   └── events.csv
│   ├── output/
│   └── reports/
├── sql/
│   └── schema.sql
├── generate_data.py
├── run_pipeline.py
├── requirements.txt
└── README.md
```

## 4. Setting Up the Project

### Requirements

- Python
- MySQL (only needed for database publishing)
- Required Python packages from `requirements.txt`

### Create and activate a virtual environment

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run the pipeline with the sample data

```powershell
python run_pipeline.py --input data/input/events.csv --output-dir data/output --report-dir data/reports --gap-minutes 30
```

This processes the sample CSV file and generates the output files.

### Generate 100,000 test records

A separate script is included to generate a larger dataset for testing.

```powershell
python generate_data.py --rows 100000 --output data/input/events_100k.csv --seed 42
```

### Run the pipeline with the larger dataset

```powershell
python run_pipeline.py --input data/input/events_100k.csv --output-dir data/output_100k --report-dir data/reports_100k --gap-minutes 30
```

### Run automated tests

```powershell
python -m pytest -v
```

## 5. MySQL Configuration

MySQL is optional. The pipeline can run using CSV files without connecting to a database.

To use MySQL, first create the database:

```sql
CREATE DATABASE clickstream_db;
```

Run the SQL commands from `sql/schema.sql` to create the required tables.

Set the database connection details in PowerShell:

```powershell
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_password"
$env:MYSQL_DATABASE="clickstream_db"
```

Then run the pipeline with MySQL publishing enabled:

```powershell
python run_pipeline.py --input data/input/events.csv --output-dir data/output --report-dir data/reports --publish-mysql
```

The project uses MySQL's `INSERT ... ON DUPLICATE KEY UPDATE` to update existing records instead of creating duplicates when the same data is processed again.

Database credentials are read from environment variables and are not stored in the source code.

## 6. Generated Output Files

After processing the input data, the pipeline generates these files:

- **sessions.csv:** Contains one row for each session, including its start time, end time, event count and duration.
- **session_events.csv:** Contains the accepted events along with their assigned session IDs.
- **rejects.csv:** Stores records that could not be processed and the reason for rejection.
- **run_report.json:** Contains details about the pipeline execution, including record counts, processing time and run status.

## 7. Data Validation and Reconciliation

I added checks to make sure the records are processed correctly.

The pipeline verifies that:

- Total input records equal accepted records plus duplicates plus rejected records.
- Every accepted event is assigned to a session.
- The number of session records matches the rows in `sessions.csv`.
- The total event count across all sessions matches the number of rows in `session_events.csv`.

These checks are also recorded in `run_report.json`.

## 8. Handling Reruns and Recovery

The project is designed so that running the same input again does not unnecessarily create duplicate output records.

- CSV output files are replaced each time the pipeline runs.
- Session IDs remain consistent for the same input events.
- MySQL uses upsert operations to handle existing records.
- If a run fails because of a configuration or database issue, it can be run again after fixing the problem.
- For historical data corrections, the affected input needs to be processed again.

One limitation is that obsolete MySQL sessions are not automatically deleted during backfills. A clean backfill currently requires clearing the affected target data or implementing a replacement strategy.

## 9. Testing and Performance

I tested the pipeline with different scenarios to check whether it handles both normal and incorrect data.

The automated tests cover:

- Normal session creation.
- Events with exactly a 30-minute gap.
- Events with a gap greater than 30 minutes.
- Events received out of order.
- Duplicate event IDs.
- Conflicting duplicate records.
- Missing timestamps.
- Invalid timestamps.
- Empty input files.

I also generated a dataset containing 100,000 events to check how the pipeline performs with a larger input.

The generator uses a fixed random seed so that the test data can be reproduced.

For datasets larger than available memory, the pipeline could be improved by processing users in separate partitions while keeping all events belonging to the same user together.

## 10. Current Limitations

There are a few things this project does not handle yet:

- It processes data in batches rather than continuously.
- It does not automatically repair sessions when late events arrive in a later batch.
- Timestamps without timezone information are assumed to be UTC.
- MySQL publishing requires a running and accessible database.
- It does not automatically remove outdated MySQL sessions during backfills.

In the future, the project could be improved with better logging, monitoring, database transaction handling and automatic recovery for late-arriving events.

## 11. Design Decisions

I chose Python because it makes data processing and validation straightforward. CSV files make it easy to inspect the input and output, while MySQL provides an option for storing processed results.

I kept the pipeline divided into separate modules so that ingestion, validation, session creation and database publishing can be maintained independently.

I also used deterministic session IDs and event sorting to make the results consistent when the same input is processed again.

The main focus of this project is to process clickstream events accurately, handle incorrect data safely and make the results easy to verify.