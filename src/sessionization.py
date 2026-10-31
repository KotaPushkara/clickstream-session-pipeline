import hashlib
from collections import defaultdict

def stable_session_id(user_id, first_event_id):
    digest = hashlib.sha256(f"{user_id}|{first_event_id}".encode("utf-8")).hexdigest()[:20]
    return f"session_{digest}"

def build_sessions(events, gap_minutes=30):
    """Assign sessions using event-time gaps. A gap > threshold starts a new session."""
    if gap_minutes < 0:
        raise ValueError("gap_minutes must be >= 0")

    by_user = defaultdict(list)
    for event in events:
        by_user[event["user_id"]].append(event)

    session_rows, session_event_rows = [], []
    for user_id in sorted(by_user):
        ordered = sorted(
            by_user[user_id],
            key=lambda e: (e["event_timestamp_parsed"], e["event_id"])
        )
        current = []
        previous_time = None

        def flush(group):
            if not group:
                return
            first, last = group[0], group[-1]
            session_id = stable_session_id(user_id, first["event_id"])
            start, end = first["event_timestamp_parsed"], last["event_timestamp_parsed"]
            session_rows.append({
                "session_id": session_id,
                "user_id": user_id,
                "session_start": start.isoformat(),
                "session_end": end.isoformat(),
                "event_count": len(group),
                "duration_seconds": int((end - start).total_seconds()),
                "first_event_id": first["event_id"],
                "last_event_id": last["event_id"],
            })
            for event in group:
                session_event_rows.append({
                    "event_id": event["event_id"],
                    "user_id": user_id,
                    "event_type": event["event_type"],
                    "event_timestamp": event["event_timestamp_parsed"].isoformat(),
                    "session_id": session_id,
                    "source_file": event.get("source_file", ""),
                    "source_row_number": event.get("source_row_number", ""),
                })

        for event in ordered:
            event_time = event["event_timestamp_parsed"]
            if previous_time is not None:
                gap = (event_time - previous_time).total_seconds() / 60
                if gap > gap_minutes:
                    flush(current)
                    current = []
            current.append(event)
            previous_time = event_time
        flush(current)

    session_rows.sort(key=lambda r: (r["user_id"], r["session_start"], r["session_id"]))
    session_event_rows.sort(key=lambda r: (r["user_id"], r["event_timestamp"], r["event_id"]))
    return session_rows, session_event_rows
