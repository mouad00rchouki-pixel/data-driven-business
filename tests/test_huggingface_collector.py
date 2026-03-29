"""Simple manual test for the Hugging Face collector.

This file is intentionally beginner-friendly. You can run it directly:

    python -m tests.test_huggingface_collector
"""

from pprint import pprint

from app.collectors.huggingface_collector import HuggingFaceCollector


def main() -> None:
    """Collect a few rows and print them."""

    collector = HuggingFaceCollector()
    records = collector.collect(max_models=5)

    print(f"Hugging Face collector returned {len(records)} records.")
    pprint(records[:2])


if __name__ == "__main__":
    main()
