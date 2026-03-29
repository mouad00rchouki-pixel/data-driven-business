"""Generate a markdown digest report from the SQLite database.

This script is useful when you want a report without calling the API.
"""

from app.database import SessionLocal, init_db
from app.services.collection_service import CollectionService
from app.utils.report_generator import ReportGenerator


def main() -> None:
    """Generate the latest markdown report and print the saved path."""

    init_db()
    db = SessionLocal()

    try:
        collection_service = CollectionService(db)
        report_generator = ReportGenerator(collection_service)
        report_data = report_generator.generate_markdown_report()

        print("Markdown report generated successfully.")
        print(f"Title: {report_data['title']}")
        print(f"Saved to: {report_data['report_path']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
