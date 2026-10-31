import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .ingestion import read_events
from .validation import validate_and_deduplicate
from .sessionization import build_sessions
from .publishing import (write_csv, write_json, SESSION_FIELDS, SESSION_EVENT_FIELDS,
                         REJECT_FIELDS, publish_mysql)

def run_pipeline(input_path, output_dir, report_dir, gap_minutes=30, publish_to_mysql=False):
    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)
    clock_start = time.perf_counter()
    report = {
        "run_id": run_id, "status": "running", "started_at": started.isoformat(),
        "input_file": str(input_path), "gap_minutes": gap_minutes,
    }
    output_dir, report_dir = Path(output_dir), Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    try:
        raw_rows, malformed = read_events(input_path)
        accepted, validation_rejects, duplicate_count = validate_and_deduplicate(raw_rows)
        rejects = malformed + validation_rejects
        sessions, session_events = build_sessions(accepted, gap_minutes)

        write_csv(output_dir / "sessions.csv", sessions, SESSION_FIELDS)
        write_csv(output_dir / "session_events.csv", session_events, SESSION_EVENT_FIELDS)
        write_csv(output_dir / "rejects.csv", rejects, REJECT_FIELDS)

        if publish_to_mysql:
            mysql_config = {
                "host": os.getenv("MYSQL_HOST", "localhost"),
                "port": int(os.getenv("MYSQL_PORT", "3306")),
                "user": os.getenv("MYSQL_USER", "root"),
                "password": os.getenv("MYSQL_PASSWORD", ""),
                "database": os.getenv("MYSQL_DATABASE", "clickstream_db"),
            }
            publish_mysql(sessions, session_events, mysql_config)

        reconciliation = {
            "input_rows": len(raw_rows) + len(malformed),
            "accepted_unique_rows": len(accepted),
            "exact_duplicate_rows": duplicate_count,
            "rejected_rows": len(rejects),
            "session_rows": len(sessions),
            "session_event_rows": len(session_events),
            "accepted_equals_session_events": len(accepted) == len(session_events),
            "session_event_count_reconciles": sum(s["event_count"] for s in sessions) == len(session_events),
            "input_count_reconciles": len(raw_rows) + len(malformed) == len(accepted) + duplicate_count + len(rejects),
        }
        report.update(reconciliation)
        report["status"] = "success"
        report["output_dir"] = str(output_dir)
    except Exception as exc:
        report["status"] = "failed"
        report["failure_reason"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["ended_at"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_seconds"] = round(time.perf_counter() - clock_start, 6)
        write_json(report_dir / "run_report.json", report)

    return report
