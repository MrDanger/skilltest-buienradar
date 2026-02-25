"""Collect Buienradar snapshots repeatedly for a fixed duration.

This is useful for demoing the ingestion process without relying on the scheduler endpoint.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.services.ingestion import ingest_latest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=60, help="Total runtime in minutes")
    parser.add_argument("--interval", type=int, default=20, help="Polling interval in minutes")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    deadline = datetime.now(timezone.utc) + timedelta(minutes=max(1, args.minutes))
    interval_seconds = max(1, args.interval) * 60

    run = 1
    while datetime.now(timezone.utc) < deadline:
        db = SessionLocal()
        try:
            result = ingest_latest(db)
            print(
                f"run={run} stations_upserted={result.stations_upserted} "
                f"measurements_inserted={result.measurements_inserted}"
            )
        finally:
            db.close()

        run += 1
        if datetime.now(timezone.utc) < deadline:
            time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
