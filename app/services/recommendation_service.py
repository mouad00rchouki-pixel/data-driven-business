"""Recommendation service.

This service combines:
- normalization
- commercial-use filtering
- profile scoring
- top model selection
- human-readable justification text

We keep the output simple because the API and dashboard will use it later.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import RecommendationResult
from app.utils.license_filter import filter_records_for_commercial_use
from app.utils.normalization import add_normalized_metrics, is_valid_number
from app.utils.scoring import PROFILE_DEFINITIONS, add_profile_scores, validate_profile_name


class RecommendationService:
    """Generate recommendations from collected model records."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def prepare_records(self, records: list[dict]) -> list[dict]:
        """Add normalized metrics and profile scores."""

        prepared_records = [record.copy() for record in records]
        prepared_records = add_normalized_metrics(prepared_records)
        prepared_records = add_profile_scores(prepared_records)
        return prepared_records

    def recommend(
        self,
        records: list[dict],
        profile_name: str,
        commercial_use: bool = False,
        top_n: int = 3,
    ) -> list[dict]:
        """Return the best models for one profile."""

        validate_profile_name(profile_name)
        prepared_records = self.prepare_records(records)

        if commercial_use:
            prepared_records = filter_records_for_commercial_use(prepared_records)

        profile_score_field = f"{profile_name}_score"
        scored_records = [
            record
            for record in prepared_records
            if record.get(profile_score_field) is not None
        ]

        scored_records.sort(
            key=lambda record: record[profile_score_field],
            reverse=True,
        )

        top_records = scored_records[:top_n]

        recommendations = []
        for rank_position, record in enumerate(top_records, start=1):
            recommendations.append(
                {
                    "rank": rank_position,
                    "model_name": record["model_name"],
                    "profile_name": profile_name,
                    "profile_score": record[profile_score_field],
                    "license_type": record.get("license_type"),
                    "source_names": record.get("source_names", []),
                    "justification": self.build_justification(record, profile_name),
                }
            )

        return recommendations

    def save_recommendations(
        self,
        collection_run_id: int,
        recommendations: list[dict],
        model_id_lookup: dict[str, int],
        commercial_use: bool,
    ) -> None:
        """Save recommendation results for later inspection.

        This is optional for the challenge, but useful for persistence.
        """

        if self.db is None:
            return

        for recommendation in recommendations:
            model_id = model_id_lookup.get(recommendation["model_name"])
            if model_id is None:
                continue

            row = RecommendationResult(
                collection_run_id=collection_run_id,
                model_id=model_id,
                profile_name=recommendation["profile_name"],
                commercial_use=commercial_use,
                profile_score=recommendation["profile_score"],
                rank_position=recommendation["rank"],
                justification_text=recommendation["justification"],
            )
            self.db.add(row)

        self.db.commit()

    def build_justification(self, record: dict, profile_name: str) -> str:
        """Create a short explanation for why a model was recommended."""

        weights = PROFILE_DEFINITIONS[profile_name]["weights"]
        strongest_metrics: list[tuple[str, float]] = []

        for metric_name, weight in weights.items():
            metric_value = record.get(metric_name)
            if metric_value is None:
                continue
            if not is_valid_number(metric_value):
                continue

            strongest_metrics.append((metric_name, metric_value))

        strongest_metrics.sort(key=lambda item: item[1], reverse=True)
        top_metrics = strongest_metrics[:3]

        if not top_metrics:
            return (
                "Recommended because it has enough available metrics to be scored, "
                "but some source data is missing."
            )

        readable_metric_names = {
            "intelligence_score_normalized": "strong benchmark intelligence",
            "tokens_per_second_normalized": "high generation speed",
            "ttft_seconds_normalized": "low latency",
            "input_price_per_1m_tokens_normalized": "low input cost",
            "output_price_per_1m_tokens_normalized": "low output cost",
            "context_window_normalized": "large context window",
        }

        explanation_parts = []
        for metric_name, _ in top_metrics:
            explanation_parts.append(
                readable_metric_names.get(metric_name, metric_name)
            )

        metric_summary = ", ".join(explanation_parts)
        return (
            f"This model scores well for the '{profile_name}' profile because it shows "
            f"{metric_summary}."
        )
