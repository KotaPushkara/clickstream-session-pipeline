from src.validation import validate_and_deduplicate
from src.sessionization import build_sessions

def make(event_id, ts, user="u1"):
    return {"event_id": event_id, "user_id": user, "event_type": "view",
            "event_timestamp": ts, "source_file": "test.csv", "source_row_number": 2}

def transform(rows, gap=30):
    accepted, rejects, duplicates = validate_and_deduplicate(rows)
    assert not rejects
    return build_sessions(accepted, gap)

def test_happy_path_and_out_of_order_events():
    sessions, events = transform([
        make("e3", "2026-01-01T10:20:00Z"),
        make("e1", "2026-01-01T10:00:00Z"),
        make("e2", "2026-01-01T10:10:00Z"),
    ])
    assert len(sessions) == 1
    assert sessions[0]["event_count"] == 3
    assert [e["event_id"] for e in events] == ["e1", "e2", "e3"]

def test_exact_threshold_stays_in_same_session():
    sessions, _ = transform([
        make("e1", "2026-01-01T10:00:00Z"),
        make("e2", "2026-01-01T10:30:00Z"),
    ])
    assert len(sessions) == 1

def test_gap_over_threshold_starts_new_session():
    sessions, _ = transform([
        make("e1", "2026-01-01T10:00:00Z"),
        make("e2", "2026-01-01T10:30:01Z"),
    ])
    assert len(sessions) == 2

def test_empty_input():
    assert build_sessions([], 30) == ([], [])

def test_users_are_isolated():
    sessions, _ = transform([
        make("e1", "2026-01-01T10:00:00Z", "u1"),
        make("e2", "2026-01-01T10:01:00Z", "u2"),
    ])
    assert len(sessions) == 2
