"""Scoring utilities and profile definitions.

The project needs several enterprise profiles with different priorities.
We use a weighted-average approach because it is easy to explain:

1. normalize every metric to 0-100
2. assign a weight to each metric based on the profile
3. compute a weighted average using only available metrics

We do not treat missing values as zero.
"""

from __future__ import annotations

import math


PROFILE_DEFINITIONS: dict[str, dict] = {
    "coding_dev": {
        "description": "Best for software engineering, code generation, and coding workflows.",
        "weights": {
            "intelligence_score_normalized": 0.40,
            "tokens_per_second_normalized": 0.20,
            "ttft_seconds_normalized": 0.15,
            "input_price_per_1m_tokens_normalized": 0.10,
            "output_price_per_1m_tokens_normalized": 0.10,
            "context_window_normalized": 0.05,
        },
    },
    "reasoning_analysis": {
        "description": "Best for reasoning-heavy tasks, analysis, and difficult problem solving.",
        "weights": {
            "intelligence_score_normalized": 0.60,
            "ttft_seconds_normalized": 0.10,
            "tokens_per_second_normalized": 0.10,
            "input_price_per_1m_tokens_normalized": 0.10,
            "output_price_per_1m_tokens_normalized": 0.10,
        },
    },
    "enterprise_agents": {
        "description": "Balanced profile for agent workflows with cost, speed, and reasoning tradeoffs.",
        "weights": {
            "intelligence_score_normalized": 0.30,
            "tokens_per_second_normalized": 0.20,
            "ttft_seconds_normalized": 0.15,
            "input_price_per_1m_tokens_normalized": 0.15,
            "output_price_per_1m_tokens_normalized": 0.10,
            "context_window_normalized": 0.10,
        },
    },
    "long_context_rag": {
        "description": "Best for retrieval and long documents where context window matters most.",
        "weights": {
            "context_window_normalized": 0.40,
            "intelligence_score_normalized": 0.25,
            "input_price_per_1m_tokens_normalized": 0.10,
            "output_price_per_1m_tokens_normalized": 0.10,
            "tokens_per_second_normalized": 0.10,
            "ttft_seconds_normalized": 0.05,
        },
    },
    "minimum_cost": {
        "description": "Best for keeping inference cost low.",
        "weights": {
            "input_price_per_1m_tokens_normalized": 0.45,
            "output_price_per_1m_tokens_normalized": 0.35,
            "tokens_per_second_normalized": 0.10,
            "ttft_seconds_normalized": 0.05,
            "intelligence_score_normalized": 0.05,
        },
    },
}


def get_available_profiles() -> list[dict]:
    """Return the list of available profile names, descriptions, and weights."""

    profiles = []
    for profile_name, profile_definition in PROFILE_DEFINITIONS.items():
        profiles.append(
            {
                "profile_name": profile_name,
                "description": profile_definition["description"],
                "weights": profile_definition["weights"],
            }
        )
    return profiles


def validate_profile_name(profile_name: str) -> None:
    """Raise a clear error if the profile name is not supported."""

    if profile_name not in PROFILE_DEFINITIONS:
        available_profiles = ", ".join(PROFILE_DEFINITIONS.keys())
        raise ValueError(
            f"Unknown profile '{profile_name}'. Available profiles: {available_profiles}"
        )


def calculate_weighted_score(
    record: dict,
    weights: dict[str, float],
) -> float | None:
    """Calculate a weighted score using only metrics that exist.

    Example:
    If a profile uses 6 metrics but a model only has 4 available, we compute
    the weighted average over those 4 metrics only.
    """

    weighted_sum = 0.0
    used_weight_sum = 0.0

    for metric_name, weight in weights.items():
        metric_value = record.get(metric_name)
        if metric_value is None:
            continue
        if isinstance(metric_value, (int, float)) and math.isnan(float(metric_value)):
            continue

        weighted_sum += metric_value * weight
        used_weight_sum += weight

    if used_weight_sum == 0:
        return None

    return round(weighted_sum / used_weight_sum, 2)


def add_profile_scores(records: list[dict]) -> list[dict]:
    """Add one score field per enterprise profile to every record."""

    for profile_name, profile_definition in PROFILE_DEFINITIONS.items():
        profile_score_field = f"{profile_name}_score"
        weights = profile_definition["weights"]

        for record in records:
            record[profile_score_field] = calculate_weighted_score(record, weights)

    return records
