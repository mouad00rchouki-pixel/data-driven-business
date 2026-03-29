"""Normalization helpers for model metrics.

The challenge asks us to convert different metrics into a shared 0-100 scale.
This file keeps that logic reusable and easy to explain.

Important idea:
- some metrics are "higher is better"
- some metrics are "lower is better"
- missing values stay as None
"""

from __future__ import annotations

import math
from typing import Iterable


def is_valid_number(value: float | None) -> bool:
    """Return True only for real numeric values that are not NaN."""

    if value is None:
        return False

    try:
        return not math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def filter_numeric_values(values: Iterable[float | None]) -> list[float]:
    """Return only real numeric values from a mixed list."""

    return [float(value) for value in values if is_valid_number(value)]


def normalize_higher_is_better(
    value: float | None,
    min_value: float,
    max_value: float,
) -> float | None:
    """Normalize a metric where larger values are better.

    Example:
    - intelligence score
    - tokens per second
    - context window
    """

    if value is None:
        return None
    if not is_valid_number(value):
        return None

    if max_value == min_value:
        return 50.0

    return round(((value - min_value) / (max_value - min_value)) * 100, 2)


def normalize_lower_is_better(
    value: float | None,
    min_value: float,
    max_value: float,
) -> float | None:
    """Normalize a metric where smaller values are better.

    Example:
    - input token price
    - output token price
    - time to first token
    """

    if value is None:
        return None
    if not is_valid_number(value):
        return None

    if max_value == min_value:
        return 50.0

    return round(((max_value - value) / (max_value - min_value)) * 100, 2)


def calculate_metric_bounds(
    records: list[dict],
    metric_name: str,
) -> tuple[float | None, float | None]:
    """Find min and max values for one metric across many records."""

    numeric_values = filter_numeric_values(
        record.get(metric_name) for record in records
    )

    if not numeric_values:
        return None, None

    return min(numeric_values), max(numeric_values)


def add_normalized_metrics(records: list[dict]) -> list[dict]:
    """Add normalized metric fields to every collected model record.

    We do this in one pass per metric:
    1. calculate the global min/max for that metric
    2. normalize every model value against that range
    """

    higher_is_better_metrics = [
        "intelligence_score",
        "tokens_per_second",
        "context_window",
    ]
    lower_is_better_metrics = [
        "input_price_per_1m_tokens",
        "output_price_per_1m_tokens",
        "ttft_seconds",
    ]

    for metric_name in higher_is_better_metrics:
        min_value, max_value = calculate_metric_bounds(records, metric_name)
        normalized_field_name = f"{metric_name}_normalized"

        for record in records:
            if min_value is None or max_value is None:
                record[normalized_field_name] = None
            else:
                record[normalized_field_name] = normalize_higher_is_better(
                    record.get(metric_name),
                    min_value=min_value,
                    max_value=max_value,
                )

    for metric_name in lower_is_better_metrics:
        min_value, max_value = calculate_metric_bounds(records, metric_name)
        normalized_field_name = f"{metric_name}_normalized"

        for record in records:
            if min_value is None or max_value is None:
                record[normalized_field_name] = None
            else:
                record[normalized_field_name] = normalize_lower_is_better(
                    record.get(metric_name),
                    min_value=min_value,
                    max_value=max_value,
                )

    return records
