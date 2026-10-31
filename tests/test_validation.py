from src.validation import validate_and_deduplicate

def row(event_id="e1", user_id="u1", event_type="view", ts="2026-01-01T10:00:00Z"):
    return {"event_id": event_id, "user_id": user_id, "event_type": event_type,
            "event_timestamp": ts, "source_file": "test.csv", "source_row_number": 2}

def test_exact_duplicate_is_skipped():
    accepted, rejects, duplicates = validate_and_deduplicate([row(), row()])
    assert len(accepted) == 1
    assert rejects == []
    assert duplicates == 1

def test_conflicting_duplicate_is_rejected():
    accepted, rejects, duplicates = validate_and_deduplicate([row(), row(event_type="purchase")])
    assert len(accepted) == 1
    assert duplicates == 0
    assert "duplicate_key_conflict" in rejects[0]["reject_reason"]

def test_missing_timestamp_is_rejected():
    accepted, rejects, duplicates = validate_and_deduplicate([row(ts="")])
    assert accepted == []
    assert "missing_required_field" in rejects[0]["reject_reason"]

def test_invalid_timestamp_is_rejected():
    accepted, rejects, duplicates = validate_and_deduplicate([row(ts="yesterday")])
    assert accepted == []
    assert "invalid_timestamp" in rejects[0]["reject_reason"]
