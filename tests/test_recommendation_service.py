"""Manual test for normalization and recommendation logic.

Run it with:

    python -m tests.test_recommendation_service
"""

from pprint import pprint

from app.collectors.orchestrator import CollectorOrchestrator
from app.services.recommendation_service import RecommendationService
from app.utils.scoring import get_available_profiles


def main() -> None:
    """Run a small end-to-end recommendation test."""

    orchestrator = CollectorOrchestrator()
    recommendation_service = RecommendationService()

    result = orchestrator.collect_all(max_models_per_source=20)
    merged_records = result["merged_records"]

    print(f"Collected merged records: {len(merged_records)}")
    print("\nAvailable profiles:")
    pprint(get_available_profiles())

    print("\nTop coding_dev recommendations:")
    recommendations = recommendation_service.recommend(
        records=merged_records,
        profile_name="coding_dev",
        commercial_use=False,
        top_n=3,
    )
    pprint(recommendations)


if __name__ == "__main__":
    main()
