from datetime import datetime, timezone

def parse_event_timestamp(value):
    if value is None or not str(value).strip():
        raise ValueError("missing_required_field: event_timestamp")
    raw = str(value).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_timestamp: expected ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def validate_and_deduplicate(rows):
    accepted, rejects = [], []
    seen = {}
    exact_duplicates = 0

    for row in rows:
        reason = None
        for field in ("event_id", "user_id", "event_type", "event_timestamp"):
            if row.get(field) is None or not str(row.get(field)).strip():
                reason = f"missing_required_field: {field}"
                break
        parsed = None
        if reason is None:
            try:
                parsed = parse_event_timestamp(row["event_timestamp"])
            except ValueError as exc:
                reason = str(exc)

        if reason:
            rejects.append(_reject(row, reason))
            continue

        normalized = dict(row)
        normalized["event_id"] = str(row["event_id"]).strip()
        normalized["user_id"] = str(row["user_id"]).strip()
        normalized["event_type"] = str(row["event_type"]).strip()
        normalized["event_timestamp_parsed"] = parsed

        event_id = normalized["event_id"]
        # Compare business fields, not source row metadata.
        fingerprint = (normalized["user_id"], normalized["event_type"], parsed.isoformat())
        if event_id in seen:
            if seen[event_id] == fingerprint:
                exact_duplicates += 1
            else:
                rejects.append(_reject(row, "duplicate_key_conflict: event_id has different content"))
            continue
        seen[event_id] = fingerprint
        accepted.append(normalized)

    return accepted, rejects, exact_duplicates

def _reject(row, reason):
    return {
        "source_file": row.get("source_file", ""),
        "source_row_number": row.get("source_row_number", ""),
        "raw_record": repr(row),
        "reject_reason": reason,
    }
