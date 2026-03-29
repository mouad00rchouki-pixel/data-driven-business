"""Simple manual test for the second source collector.

Run it directly with:

    python -m tests.test_second_source_collector
"""

from pprint import pprint

from app.collectors.second_source_collector import SecondSourceCollector


def main() -> None:
    """Collect a few rows and print them."""

    collector = SecondSourceCollector()
    records = collector.collect(max_models=5)

    print(f"Second source collector returned {len(records)} records.")
    pprint(records[:2])


if __name__ == "__main__":
    main()
