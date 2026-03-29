"""Simple manual test for the collector orchestrator.

Run it directly with:

    python -m tests.test_orchestrator
"""

from pprint import pprint

from app.collectors.orchestrator import CollectorOrchestrator


def main() -> None:
    """Run both collectors and show merged results."""

    orchestrator = CollectorOrchestrator()
    result = orchestrator.collect_all(max_models_per_source=10)

    print(f"Total source records: {len(result['source_records'])}")
    print(f"Total merged records: {len(result['merged_records'])}")
    pprint(result["merged_records"][:3])


if __name__ == "__main__":
    main()
