from pathlib import Path

DEFAULT_GAP_MINUTES = 30
REQUIRED_COLUMNS = ("event_id", "user_id", "event_type", "event_timestamp")
BASE_DIR = Path(__file__).resolve().parents[1]
