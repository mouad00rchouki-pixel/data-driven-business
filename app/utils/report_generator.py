"""Markdown report generation helpers.

This module generates a beginner-friendly digest report from the latest
collection run stored in SQLite.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.collection_service import CollectionService
from app.services.recommendation_service import RecommendationService
from app.utils.scoring import get_available_profiles


class ReportGenerator:
    """Generate markdown reports from the latest collection run."""

    def __init__(self, collection_service: CollectionService) -> None:
        self.collection_service = collection_service
        self.recommendation_service = RecommendationService()

    def generate_markdown_report(self) -> dict[str, str]:
        """Build and save a markdown report for the latest run."""

        latest_run = self.collection_service.get_latest_collection_run()
        if latest_run is None:
            raise ValueError("No completed collection run exists yet.")

        records = self.collection_service.get_latest_run_records()
        new_models = self.collection_service.get_new_models_for_latest_run()
        generated_at = datetime.utcnow()
        coverage = self._build_metric_coverage(records)
        observations = self._build_observations(records, new_models)

        lines: list[str] = []
        lines.append("# LLM Monitoring Report")
        lines.append("")
        lines.append(f"- Generated at: {generated_at.isoformat()} UTC")
        lines.append(f"- Collection run id: {latest_run.id}")
        lines.append(f"- Total models in latest run: {len(records)}")
        lines.append(f"- Newly detected models: {len(new_models)}")
        lines.append("")
        lines.append("## Sources Used")
        lines.append("")

        source_names = sorted(
            {
                source_name
                for record in records
                for source_name in record.get("source_names", [])
            }
        )
        for source_name in source_names:
            lines.append(f"- {source_name}")

        lines.append("")
        lines.append("## Newly Detected Models")
        lines.append("")
        if new_models:
            for model_name in new_models[:20]:
                lines.append(f"- {model_name}")
        else:
            lines.append("- No new models detected in the latest run.")

        lines.append("")
        lines.append("## Metric Coverage")
        lines.append("")
        for metric_name, metric_info in coverage.items():
            lines.append(
                f"- {metric_name}: {metric_info['available_count']}/{metric_info['total_count']} "
                f"models ({metric_info['coverage_percent']}%)"
            )

        lines.append("")
        lines.append("## Top Models By Profile")
        lines.append("")

        for profile in get_available_profiles():
            profile_name = profile["profile_name"]
            lines.append(f"### {profile_name}")
            lines.append("")
            lines.append(profile["description"])
            lines.append("")
            recommendations = self.recommendation_service.recommend(
                records=records,
                profile_name=profile_name,
                commercial_use=False,
                top_n=5,
            )
            if recommendations:
                for item in recommendations:
                    lines.append(
                        f"1. {item['model_name']} | score={item['profile_score']} | "
                        f"{item['justification']}"
                    )
            else:
                lines.append("- No recommendations available.")
            lines.append("")

        lines.append("## Major Observations")
        lines.append("")
        for observation in observations:
            lines.append(f"- {observation}")
        lines.append("")

        lines.append("## Recommendation Summary")
        lines.append("")
        summary_recommendations = self.recommendation_service.recommend(
            records=records,
            profile_name="enterprise_agents",
            commercial_use=False,
            top_n=3,
        )
        if summary_recommendations:
            for item in summary_recommendations:
                lines.append(
                    f"- {item['model_name']} is a strong general choice for enterprise agents "
                    f"with score {item['profile_score']}."
                )
        else:
            lines.append("- No enterprise summary recommendations are available.")
        lines.append("")

        lines.append("## Limitations")
        lines.append("")
        lines.append("- Some models do not expose all metrics across all public sources.")
        lines.append("- Cross-source model matching uses a simple normalized-name rule.")
        lines.append("- Missing metrics are stored as null and skipped during scoring.")
        lines.append("- The first run marks all models as new because there is no earlier baseline.")
        lines.append("")

        report_content = "\n".join(lines)

        settings.resolved_reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = (
            Path(settings.resolved_reports_dir)
            / f"llm_monitoring_report_run_{latest_run.id}.md"
        )
        report_path.write_text(report_content, encoding="utf-8")

        return {
            "title": "LLM Monitoring Report",
            "generated_at": generated_at.isoformat(),
            "report_path": str(report_path),
            "content": report_content,
        }

    def _build_metric_coverage(self, records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Calculate how many models have each key metric."""

        metric_fields = {
            "intelligence_score": "intelligence_score_raw",
            "input_price_per_1m_tokens": "input_price_per_1m_tokens_raw",
            "output_price_per_1m_tokens": "output_price_per_1m_tokens_raw",
            "tokens_per_second": "tokens_per_second_raw",
            "ttft_seconds": "ttft_seconds_raw",
            "context_window": "context_window_raw",
            "license_type": "license_type",
        }

        coverage: dict[str, dict[str, Any]] = {}
        total_count = len(records)

        for display_name, field_name in metric_fields.items():
            available_count = sum(
                1 for record in records if record.get(field_name) is not None
            )
            coverage[display_name] = {
                "available_count": available_count,
                "total_count": total_count,
                "coverage_percent": round((available_count / total_count) * 100, 2)
                if total_count > 0
                else 0.0,
            }

        return coverage

    def _build_observations(
        self,
        records: list[dict[str, Any]],
        new_models: list[str],
    ) -> list[str]:
        """Create a few simple observations for the digest."""

        observations: list[str] = []
        total_models = len(records)

        records_with_license = sum(1 for record in records if record.get("license_type"))
        records_with_intelligence = sum(
            1 for record in records if record.get("intelligence_score_raw") is not None
        )
        records_with_cost = sum(
            1
            for record in records
            if record.get("input_price_per_1m_tokens_raw") is not None
            or record.get("output_price_per_1m_tokens_raw") is not None
        )

        observations.append(
            f"The latest run contains {total_models} model rows across the configured public sources."
        )
        observations.append(
            f"{records_with_intelligence} models include benchmark intelligence data, while "
            f"{records_with_cost} models include cost-related data."
        )
        observations.append(
            f"{records_with_license} models include license metadata that can be used by the commercial-use filter."
        )
        observations.append(
            f"{len(new_models)} models are flagged as new in the latest run."
        )

        return observations
