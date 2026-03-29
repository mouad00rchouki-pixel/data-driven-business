"""Collector orchestrator.

This file runs all source collectors and also produces a simple merged view.
The merged view is helpful because the challenge wants us to combine metrics
from multiple sources when possible.
"""

from __future__ import annotations

from typing import Any

from app.collectors.base import BaseCollector
from app.collectors.huggingface_collector import HuggingFaceCollector
from app.collectors.second_source_collector import SecondSourceCollector


class CollectorOrchestrator:
    """Run all collectors and merge their results by model name."""

    def __init__(self) -> None:
        self.collectors = [
            HuggingFaceCollector(),
            SecondSourceCollector(),
        ]

    def collect_all(self, max_models_per_source: int = 50) -> dict[str, list[dict[str, Any]]]:
        """Run every collector and return both raw and merged records.

        We keep going even if one source fails because partial data is better
        than no data for this challenge.
        """

        source_records: list[dict[str, Any]] = []

        for collector in self.collectors:
            try:
                records = collector.collect(max_models=max_models_per_source)
                source_records.extend(records)
                print(
                    f"{collector.source_name}: collected {len(records)} records successfully."
                )
            except Exception as collector_error:
                print(
                    f"{collector.source_name}: collection failed. "
                    f"Reason: {collector_error}"
                )

        merged_records = self.merge_records(source_records)
        return {
            "source_records": source_records,
            "merged_records": merged_records,
        }

    def merge_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Merge records from multiple sources into one model-level view.

        Merge rule:
        - models are matched by a simple normalized name
        - the first non-null value wins for each metric
        - source names are kept in a list for transparency
        """

        merged_by_model: dict[str, dict[str, Any]] = {}

        for record in records:
            model_key = BaseCollector.normalize_model_name(record["model_name"])

            if model_key not in merged_by_model:
                merged_by_model[model_key] = {
                    "model_name": record["model_name"],
                    "normalized_model_name": model_key,
                    "source_names": [record["source_name"]],
                    "intelligence_score": record.get("intelligence_score"),
                    "input_price_per_1m_tokens": record.get(
                        "input_price_per_1m_tokens"
                    ),
                    "output_price_per_1m_tokens": record.get(
                        "output_price_per_1m_tokens"
                    ),
                    "tokens_per_second": record.get("tokens_per_second"),
                    "ttft_seconds": record.get("ttft_seconds"),
                    "context_window": record.get("context_window"),
                    "license_type": record.get("license_type"),
                    "last_updated_at": record.get("last_updated_at"),
                }
                continue

            existing_record = merged_by_model[model_key]
            if record["source_name"] not in existing_record["source_names"]:
                existing_record["source_names"].append(record["source_name"])

            for field_name in [
                "intelligence_score",
                "input_price_per_1m_tokens",
                "output_price_per_1m_tokens",
                "tokens_per_second",
                "ttft_seconds",
                "context_window",
                "license_type",
                "last_updated_at",
            ]:
                if existing_record.get(field_name) is None and record.get(field_name) is not None:
                    existing_record[field_name] = record[field_name]

        return list(merged_by_model.values())
