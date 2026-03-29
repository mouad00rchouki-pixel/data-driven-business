"""Collector for the public Vellum LLM leaderboard.

Source used:
- https://vellum.ai/llm-leaderboard

Why this source:
- it exposes cost, speed, latency, and context window on a public page
- it complements Hugging Face, which mainly gives benchmark intelligence scores

Strategy:
1. Try parsing HTML tables with pandas.read_html.
2. If that fails, use a plain-text regex fallback on the page text.

This source does not clearly expose license information for models, so we
store the license as None instead of guessing.
"""

from __future__ import annotations

import re
from io import StringIO
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectedModelRecord
from app.config import settings


class SecondSourceCollector(BaseCollector):
    """Collect operational model metrics from Vellum."""

    source_name = "vellum_llm_leaderboard"
    SOURCE_URL = settings.second_source_url

    def collect(self, max_models: int = 50) -> list[dict[str, Any]]:
        """Collect rows from the second source with fallback logic."""

        html_text = self.fetch_text(self.SOURCE_URL)
        updated_at = self._parse_page_updated_date(html_text)

        try:
            records = self._collect_with_html_tables(
                html_text=html_text,
                updated_at=updated_at,
                max_models=max_models,
            )
        except Exception as table_error:
            print(
                "Vellum HTML table parsing failed. Falling back to regex parsing. "
                f"Reason: {table_error}"
            )
            records = self._collect_with_regex_fallback(
                html_text=html_text,
                updated_at=updated_at,
                max_models=max_models,
            )

        return self.deduplicate_records(records)[:max_models]

    def _collect_with_html_tables(
        self,
        html_text: str,
        updated_at,
        max_models: int,
    ) -> list[dict[str, Any]]:
        """Try parsing the comparison tables directly from HTML."""

        tables = pd.read_html(StringIO(html_text))
        if not tables:
            raise ValueError("No HTML tables found on the page.")

        best_table = None
        for table in tables:
            normalized_columns = [str(column).lower() for column in table.columns]
            has_context = any("context" in column for column in normalized_columns)
            has_input_cost = any("input" in column and "cost" in column for column in normalized_columns)
            has_output_cost = any("output" in column and "cost" in column for column in normalized_columns)

            if has_context and has_input_cost and has_output_cost:
                best_table = table
                break

        if best_table is None:
            raise ValueError("Could not find the Vellum comparison table.")

        records: list[dict[str, Any]] = []
        for _, row in best_table.iterrows():
            parsed_record = self._parse_vellum_table_row(row.to_dict(), updated_at)
            if parsed_record is not None:
                records.append(parsed_record.to_dict())

        return records[:max_models]

    def _collect_with_regex_fallback(
        self,
        html_text: str,
        updated_at,
        max_models: int,
    ) -> list[dict[str, Any]]:
        """Fallback parser based on page text.

        This method is less elegant than reading HTML tables, but it is useful
        if the page layout changes and the table parser stops working.
        """

        soup = BeautifulSoup(html_text, "html.parser")
        page_text = soup.get_text("\n", strip=True)
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]

        records: list[dict[str, Any]] = []
        pattern = re.compile(
            r"^(?P<model>.+?)\s+(?P<context>[\d,]+|n/a)\$(?P<input>[\d.]+|n/a)\$(?P<output>[\d.]+|n/a)\s+(?P<speed>[\d.]+ t/s|n/a)\s+(?P<latency>[\d.]+ seconds|n/a)$",
            flags=re.IGNORECASE,
        )

        for line in lines:
            match = pattern.match(line)
            if not match:
                continue

            groups = match.groupdict()
            parsed_record = CollectedModelRecord(
                model_name=groups["model"].strip(),
                source_name=self.source_name,
                intelligence_score=None,
                input_price_per_1m_tokens=self.parse_float(groups["input"]),
                output_price_per_1m_tokens=self.parse_float(groups["output"]),
                tokens_per_second=self.parse_float(groups["speed"]),
                ttft_seconds=self.parse_float(groups["latency"]),
                context_window=self.parse_float(groups["context"]),
                license_type=None,
                last_updated_at=updated_at,
            )
            records.append(parsed_record.to_dict())

            if len(records) >= max_models:
                break

        if not records:
            raise ValueError("Regex fallback could not parse any Vellum rows.")

        return records

    def _parse_vellum_table_row(
        self,
        row_data: dict[str, Any],
        updated_at,
    ) -> CollectedModelRecord | None:
        """Convert one parsed Vellum table row into our common format."""

        row_values = {str(key).strip().lower(): value for key, value in row_data.items()}

        model_name = (
            row_values.get("models")
            or row_values.get("model")
            or row_values.get("unnamed: 0")
        )
        if model_name is None:
            return None

        return CollectedModelRecord(
            model_name=str(model_name).strip(),
            source_name=self.source_name,
            intelligence_score=None,
            input_price_per_1m_tokens=self.parse_float(
                row_values.get("input cost / 1m tokens")
                or row_values.get("input cost / 1m token")
                or row_values.get("input cost / 1m")
            ),
            output_price_per_1m_tokens=self.parse_float(
                row_values.get("output cost / 1m tokens")
                or row_values.get("output cost / 1m token")
                or row_values.get("output cost / 1m")
            ),
            tokens_per_second=self.parse_float(
                row_values.get("speed (tokens/second)") or row_values.get("speed")
            ),
            ttft_seconds=self.parse_float(
                row_values.get("latency") or row_values.get("ttft")
            ),
            context_window=self.parse_float(
                row_values.get("context window") or row_values.get("context size")
            ),
            license_type=None,
            last_updated_at=updated_at,
        )

    def _parse_page_updated_date(self, html_text: str):
        """Extract the page update date if it is visible on the page."""

        match = re.search(r"updated\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})", html_text)
        if match:
            return self.parse_date(match.group(1))
        return None
