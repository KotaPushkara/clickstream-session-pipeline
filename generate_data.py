import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

def generate(rows, output, seed=42):
    rng = random.Random(seed)
    users = [f"user_{i:05d}" for i in range(max(10, rows // 100))]
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["event_id", "user_id", "event_type", "event_timestamp"])
        generated = []
        for i in range(rows):
            user = rng.choice(users)
            ts = base + timedelta(minutes=rng.randint(0, max(1, rows // 5)))
            generated.append([f"evt_{i:08d}", user, rng.choice(
                ["page_view", "product_view", "add_to_cart", "purchase", "login"]), ts.isoformat()])
        # Keep data deterministic; a small portion is intentionally out of order by source row.
        rng.shuffle(generated)
        for record in generated:
            writer.writerow(record)
        # Add labelled quality examples when the requested size allows it.
        if rows >= 20:
            writer.writerow(["evt_invalid_missing_ts", "user_bad", "page_view", ""])
            writer.writerow(["evt_invalid_bad_ts", "user_bad", "page_view", "not-a-timestamp"])
            writer.writerow(generated[0])  # exact duplicate event
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--output", default="data/input/events_generated.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.rows < 0:
        parser.error("--rows must be >= 0")
    print(f"Generated: {generate(args.rows, args.output, args.seed)}")
