import csv
import json
from pathlib import Path

SESSION_FIELDS = ["session_id", "user_id", "session_start", "session_end", "event_count",
                  "duration_seconds", "first_event_id", "last_event_id"]
SESSION_EVENT_FIELDS = ["event_id", "user_id", "event_type", "event_timestamp",
                        "session_id", "source_file", "source_row_number"]
REJECT_FIELDS = ["source_file", "source_row_number", "raw_record", "reject_reason"]

def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def publish_mysql(session_rows, session_event_rows, config):
    """Optional idempotent MySQL upsert. Credentials are read from environment."""
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError("mysql-connector-python is required for --publish-mysql") from exc

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor()
        session_sql = """
            INSERT INTO sessions
            (session_id, user_id, session_start, session_end, event_count, duration_seconds,
             first_event_id, last_event_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE user_id=VALUES(user_id), session_start=VALUES(session_start),
            session_end=VALUES(session_end), event_count=VALUES(event_count),
            duration_seconds=VALUES(duration_seconds), first_event_id=VALUES(first_event_id),
            last_event_id=VALUES(last_event_id)
        """
        event_sql = """
            INSERT INTO session_events
            (event_id, user_id, event_type, event_timestamp, session_id, source_file, source_row_number)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE user_id=VALUES(user_id), event_type=VALUES(event_type),
            event_timestamp=VALUES(event_timestamp), session_id=VALUES(session_id),
            source_file=VALUES(source_file), source_row_number=VALUES(source_row_number)
        """
        cursor.executemany(session_sql, [tuple(r[k] for k in SESSION_FIELDS) for r in session_rows])
        cursor.executemany(event_sql, [tuple(r[k] for k in SESSION_EVENT_FIELDS) for r in session_event_rows])
        connection.commit()
        cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
