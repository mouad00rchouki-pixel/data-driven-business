"""Collector for the Hugging Face Open LLM Leaderboard dataset.

Source used:
- https://huggingface.co/datasets/open-llm-leaderboard/contents

Strategy:
1. Try the Hugging Face datasets rows API first.
2. If that fails, download the public parquet file directly.

This source is great for benchmark-style intelligence scores and license data,
but it does not provide cost, latency, or throughput for most models.
We store those fields as None instead of inventing values.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
import requests

from app.collectors.base import BaseCollector, CollectedModelRecord


class HuggingFaceCollector(BaseCollector):
    """Collect benchmark and metadata from the Hugging Face leaderboard."""

    source_name = "huggingface_open_llm_leaderboard"

    DATASET_ROWS_API_URL = "https://datasets-server.huggingface.co/rows"
    DATASET_NAME = "open-llm-leaderboard/contents"
    DATASET_CONFIG = "default"
    DATASET_SPLIT = "train"
    PARQUET_FALLBACK_URL = (
        "https://huggingface.co/datasets/open-llm-leaderboard/contents/"
        "resolve/main/data/train-00000-of-00001.parquet?download=true"
    )

    def collect(self, max_models: int = 50) -> list[dict[str, Any]]:
        """Collect records from Hugging Face.

        We first try the official dataset rows endpoint because it returns
        clean JSON. If that request fails, we fall back to the public parquet.
        """

        try:
            records = self._collect_from_rows_api(max_models=max_models)
        except Exception as api_error:
            print(
                "Hugging Face rows API failed. Falling back to parquet download. "
                f"Reason: {api_error}"
            )
            records = self._collect_from_parquet(max_models=max_models)

        return self.deduplicate_records(records)[:max_models]

    def _collect_from_rows_api(self, max_models: int) -> list[dict[str, Any]]:
        """Fetch records using the Hugging Face datasets rows API."""

        offset = 0
        page_size = min(max_models * 3, 100)
        collected_rows: list[dict[str, Any]] = []

        while len(collected_rows) < max_models * 2:
            payload = self.fetch_json(
                self.DATASET_ROWS_API_URL,
                params={
                    "dataset": self.DATASET_NAME,
                    "config": self.DATASET_CONFIG,
                    "split": self.DATASET_SPLIT,
                    "offset": offset,
                    "length": page_size,
                },
            )

            rows = payload.get("rows", [])
            if not rows:
                break

            for row_item in rows:
                row_data = row_item.get("row", {})
                parsed_record = self._parse_huggingface_row(row_data)
                if parsed_record is not None:
                    collected_rows.append(parsed_record.to_dict())

            offset += page_size

            if len(rows) < page_size:
                break

        return collected_rows

    def _collect_from_parquet(self, max_models: int) -> list[dict[str, Any]]:
        """Fallback method that downloads the public parquet file.

        We use pandas here because the parquet file is already tabular and easy
        to work with once loaded.
        """

        response = requests.get(
            self.PARQUET_FALLBACK_URL,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        dataframe = pd.read_parquet(BytesIO(response.content))
        records: list[dict[str, Any]] = []

        for _, row in dataframe.head(max_models * 3).iterrows():
            parsed_record = self._parse_huggingface_row(row.to_dict())
            if parsed_record is not None:
                records.append(parsed_record.to_dict())

        return records

    def _parse_huggingface_row(
        self, row_data: dict[str, Any]
    ) -> CollectedModelRecord | None:
        """Convert one Hugging Face row into our common format."""

        model_name = row_data.get("fullname") or row_data.get("Base Model")
        if not model_name:
            return None

        intelligence_score = self.parse_float(row_data.get("Average ⬆️"))
        license_type = row_data.get("Hub License") or None
        submission_date = row_data.get("Submission Date")
        upload_date = row_data.get("Upload To Hub Date")

        return CollectedModelRecord(
            model_name=str(model_name).strip(),
            source_name=self.source_name,
            intelligence_score=intelligence_score,
            input_price_per_1m_tokens=None,
            output_price_per_1m_tokens=None,
            tokens_per_second=None,
            ttft_seconds=None,
            context_window=None,
            license_type=str(license_type).strip() if license_type else None,
            last_updated_at=self.parse_date(submission_date)
            or self.parse_date(upload_date),
        )
