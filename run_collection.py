"""Simple entry script for manual collection runs.

This script is useful during development because it lets us trigger a full
collection and store the result in SQLite without starting the API server.
"""

from pprint import pprint

from app.database import SessionLocal, init_db
from app.services.collection_service import CollectionService


def main() -> None:
    """Run a full persisted collection and print a short summary."""

    init_db()
    db = SessionLocal()

    try:
        collection_service = CollectionService(db)
        result = collection_service.run_collection(max_models_per_source=25)

        print("\nCollection finished and was saved to SQLite.")
        print(f"Collection run id: {result['collection_run_id']}")
        print(f"Status: {result['status']}")
        print(f"Stored source records: {result['source_record_count']}")
        print(f"Merged record count: {result['merged_record_count']}")
        print(f"New models detected: {result['new_model_count']}")
        print("\nFirst detected new models:")
        pprint(result["new_models"][:10])
    finally:
        db.close()


if __name__ == "__main__":
    main()
