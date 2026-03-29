"""Simple script-based scheduler for repeated collection runs.

Why this approach:
- no extra dependency is required
- easy to explain in an interview
- good enough for a local demo

How it works:
- run one collection immediately
- sleep for a configurable number of minutes
- run again forever until stopped with Ctrl + C
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime

from app.database import SessionLocal, init_db
from app.services.collection_service import CollectionService


def run_collection_once(max_models_per_source: int) -> None:
    """Run one persisted collection and print a short summary."""

    db = SessionLocal()

    try:
        service = CollectionService(db)
        result = service.run_collection(max_models_per_source=max_models_per_source)

        print(
            f"[{datetime.utcnow().isoformat()} UTC] "
            f"Run {result['collection_run_id']} completed | "
            f"records={result['source_record_count']} | "
            f"new_models={result['new_model_count']}"
        )
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the scheduler."""

    parser = argparse.ArgumentParser(
        description="Run the LLM collection job repeatedly on a fixed interval."
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=60,
        help="How often to rerun the collection job.",
    )
    parser.add_argument(
        "--max-models-per-source",
        type=int,
        default=25,
        help="How many models to request from each source on every run.",
    )
    return parser.parse_args()


def main() -> None:
    """Start the simple scheduler loop."""

    args = parse_args()
    init_db()

    print("Starting simple collection scheduler.")
    print(f"Interval: {args.interval_minutes} minute(s)")
    print(f"Max models per source: {args.max_models_per_source}")
    print("Press Ctrl + C to stop.")

    try:
        while True:
            run_collection_once(max_models_per_source=args.max_models_per_source)
            sleep_seconds = args.interval_minutes * 60
            print(f"Sleeping for {args.interval_minutes} minute(s)...")
            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        print("\nScheduler stopped by user.")


if __name__ == "__main__":
    main()
