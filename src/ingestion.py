import csv
from pathlib import Path

def read_events(input_path):
    """Read CSV rows while preserving source filename and 1-based CSV row number."""
    path = Path(input_path)
    rows = []
    malformed = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return rows, malformed
        for row_number, row in enumerate(reader, start=2):
            # DictReader stores surplus fields under key None.
            if None in row:
                malformed.append({
                    "source_file": path.name,
                    "source_row_number": row_number,
                    "raw_record": repr(row),
                    "reject_reason": "malformed_row: unexpected extra columns",
                })
                continue
            rows.append({
                "event_id": row.get("event_id"),
                "user_id": row.get("user_id"),
                "event_type": row.get("event_type"),
                "event_timestamp": row.get("event_timestamp"),
                "source_file": path.name,
                "source_row_number": row_number,
            })
    return rows, malformed
