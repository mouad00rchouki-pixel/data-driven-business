"""Shared collector utilities.

This file contains:

- a simple dataclass that represents one collected model record
- a base collector class with common request and parsing helpers

The goal is to keep each source collector small and readable.
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import requests

from app.config import settings


@dataclass
class CollectedModelRecord:
    """Simple normalized Python object used by all collectors.

    We keep this object intentionally small and close to the challenge fields.
    Later phases can store these values in the database.
    """

    model_name: str
    source_name: str
    intelligence_score: float | None = None
    input_price_per_1m_tokens: float | None = None
    output_price_per_1m_tokens: float | None = None
    tokens_per_second: float | None = None
    ttft_seconds: float | None = None
    context_window: float | None = None
    license_type: str | None = None
    last_updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the dataclass into a plain dictionary."""

        return asdict(self)


class BaseCollector(ABC):
    """Base class that all collectors inherit from."""

    source_name: str = "unknown_source"

    def __init__(self, timeout_seconds: int | None = None) -> None:
        self.timeout_seconds = timeout_seconds or settings.request_timeout_seconds

    @abstractmethod
    def collect(self, max_models: int = 50) -> list[dict[str, Any]]:
        """Collect records from one source."""

    def fetch_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Fetch JSON data with basic timeout and error handling."""

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def fetch_text(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Fetch plain text or HTML content."""

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.text

    @staticmethod
    def normalize_model_name(model_name: str) -> str:
        """Create a simple comparable key for model matching.

        We keep the logic deterministic and easy to explain:
        lowercase the name, replace separators with spaces, remove
        duplicate spaces, and trim the result.
        """

        cleaned_name = model_name.lower()
        cleaned_name = cleaned_name.replace("_", " ").replace("-", " ")
        cleaned_name = re.sub(r"\s+", " ", cleaned_name)
        return cleaned_name.strip()

    @staticmethod
    def parse_float(value: Any) -> float | None:
        """Convert a value into a float when possible.

        This helper handles strings such as:
        - "1,000,000"
        - "$1.25"
        - "67 t/s"
        - "1.6 seconds"
        - "0.003s"
        """

        if value is None:
            return None

        if isinstance(value, (int, float)):
            numeric_value = float(value)
            if math.isnan(numeric_value):
                return None
            return numeric_value

        text = str(value).strip().lower()
        if not text or text in {"n/a", "na", "-", "--", "none"}:
            return None

        text = text.replace(",", "")
        text = text.replace("$", "")
        text = text.replace("t/s", "")
        text = text.replace("seconds", "")
        text = text.replace("second", "")
        text = text.replace("s", "")
        text = text.strip()

        try:
            numeric_value = float(text)
            if math.isnan(numeric_value):
                return None
            return numeric_value
        except ValueError:
            return None

    @staticmethod
    def parse_date(value: Any) -> datetime | None:
        """Parse dates from a few common formats used by our sources."""

        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return None

        supported_formats = [
            "%Y-%m-%d",
            "%d %b %Y",
            "%B %Y",
            "%b %Y",
        ]

        for date_format in supported_formats:
            try:
                return datetime.strptime(text, date_format)
            except ValueError:
                continue

        return None

    @staticmethod
    def deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep one record per normalized model name.

        If we see the same model more than once, we keep the record with the
        highest intelligence score because that is the most useful summary
        value for the Hugging Face source.
        """

        best_records: dict[str, dict[str, Any]] = {}

        for record in records:
            model_key = BaseCollector.normalize_model_name(record["model_name"])
            current_best = best_records.get(model_key)

            if current_best is None:
                best_records[model_key] = record
                continue

            current_score = current_best.get("intelligence_score") or float("-inf")
            new_score = record.get("intelligence_score") or float("-inf")

            if new_score > current_score:
                best_records[model_key] = record

        return list(best_records.values())
