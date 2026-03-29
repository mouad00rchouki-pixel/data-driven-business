"""Collection and storage service.

This service is responsible for:
- running the collectors
- storing collection runs
- storing sources
- storing models
- storing raw and normalized metrics
- detecting newly seen models compared to the previous run

We keep the logic explicit and beginner-friendly so the flow is easy to explain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import BaseCollector
from app.collectors.orchestrator import CollectorOrchestrator
from app.models import CollectionRun, Model, ModelMetric, RecommendationResult, Source
from app.utils.normalization import add_normalized_metrics


class CollectionService:
    """Run collection jobs and persist their output in SQLite."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.orchestrator = CollectorOrchestrator()

    def run_collection(self, max_models_per_source: int = 25) -> dict[str, Any]:
        """Collect data from all sources and store it in the database."""

        collection_run = CollectionRun(
            started_at=datetime.utcnow(),
            status="started",
            notes=f"Requested max_models_per_source={max_models_per_source}",
        )
        self.db.add(collection_run)
        self.db.commit()
        self.db.refresh(collection_run)

        try:
            collection_result = self.orchestrator.collect_all(
                max_models_per_source=max_models_per_source
            )

            source_records = add_normalized_metrics(collection_result["source_records"])
            self._store_source_records(
                collection_run=collection_run,
                source_records=source_records,
            )

            new_models = self._detect_new_models(collection_run_id=collection_run.id)

            collection_run.finished_at = datetime.utcnow()
            collection_run.status = "completed"
            self.db.commit()

            return {
                "collection_run_id": collection_run.id,
                "status": collection_run.status,
                "source_record_count": len(source_records),
                "merged_record_count": len(collection_result["merged_records"]),
                "new_model_count": len(new_models),
                "new_models": new_models,
            }
        except Exception as error:
            collection_run.finished_at = datetime.utcnow()
            collection_run.status = "failed"
            collection_run.notes = f"{collection_run.notes}\nError: {error}"
            self.db.commit()
            raise

    def _store_source_records(
        self,
        collection_run: CollectionRun,
        source_records: list[dict[str, Any]],
    ) -> None:
        """Persist all collected source records for one run."""

        for record in source_records:
            source = self._get_or_create_source(record["source_name"])
            model = self._get_or_create_model(record, collection_run.id)

            source.last_collected_at = datetime.utcnow()
            if model.license_type is None and record.get("license_type"):
                model.license_type = record["license_type"]

            model_metric = ModelMetric(
                collection_run_id=collection_run.id,
                model_id=model.id,
                source_id=source.id,
                raw_model_name=record["model_name"],
                intelligence_score_raw=record.get("intelligence_score"),
                intelligence_score_normalized=record.get(
                    "intelligence_score_normalized"
                ),
                input_price_per_1m_tokens_raw=record.get("input_price_per_1m_tokens"),
                input_price_per_1m_tokens_normalized=record.get(
                    "input_price_per_1m_tokens_normalized"
                ),
                output_price_per_1m_tokens_raw=record.get("output_price_per_1m_tokens"),
                output_price_per_1m_tokens_normalized=record.get(
                    "output_price_per_1m_tokens_normalized"
                ),
                tokens_per_second_raw=record.get("tokens_per_second"),
                tokens_per_second_normalized=record.get("tokens_per_second_normalized"),
                ttft_seconds_raw=record.get("ttft_seconds"),
                ttft_seconds_normalized=record.get("ttft_seconds_normalized"),
                context_window_raw=record.get("context_window"),
                context_window_normalized=record.get("context_window_normalized"),
                license_type_raw=record.get("license_type"),
                last_updated_at=record.get("last_updated_at"),
                collected_at=datetime.utcnow(),
            )
            self.db.add(model_metric)

        self.db.commit()

    def _get_or_create_source(self, source_name: str) -> Source:
        """Create a source row only once."""

        existing_source = self.db.scalar(
            select(Source).where(Source.name == source_name)
        )
        if existing_source is not None:
            return existing_source

        source = Source(
            name=source_name,
            base_url=None,
            source_type="public_web_source",
            last_collected_at=datetime.utcnow(),
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def _get_or_create_model(
        self,
        record: dict[str, Any],
        collection_run_id: int,
    ) -> Model:
        """Create one unique model row per normalized model name."""

        normalized_model_name = BaseCollector.normalize_model_name(record["model_name"])

        existing_model = self.db.scalar(
            select(Model).where(Model.normalized_model_name == normalized_model_name)
        )
        if existing_model is not None:
            return existing_model

        model = Model(
            model_name=record["model_name"],
            normalized_model_name=normalized_model_name,
            license_type=record.get("license_type"),
            first_seen_run_id=collection_run_id,
            created_at=datetime.utcnow(),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_latest_collection_run(self) -> CollectionRun | None:
        """Return the most recent completed collection run."""

        statement = (
            select(CollectionRun)
            .where(CollectionRun.status == "completed")
            .order_by(CollectionRun.id.desc())
        )
        return self.db.scalar(statement)

    def get_previous_collection_run(self, current_run_id: int) -> CollectionRun | None:
        """Return the completed run just before the given run."""

        statement = (
            select(CollectionRun)
            .where(CollectionRun.status == "completed", CollectionRun.id < current_run_id)
            .order_by(CollectionRun.id.desc())
        )
        return self.db.scalar(statement)

    def _detect_new_models(self, collection_run_id: int) -> list[str]:
        """Return model names that are present in this run but not the previous one."""

        current_model_names = set(self._get_model_names_for_run(collection_run_id))
        previous_run = self.get_previous_collection_run(collection_run_id)

        if previous_run is None:
            return sorted(current_model_names)

        previous_model_names = set(self._get_model_names_for_run(previous_run.id))
        new_models = current_model_names - previous_model_names
        return sorted(new_models)

    def _get_model_names_for_run(self, collection_run_id: int) -> list[str]:
        """Return distinct model names for one run."""

        statement = (
            select(Model.model_name)
            .join(ModelMetric, Model.id == ModelMetric.model_id)
            .where(ModelMetric.collection_run_id == collection_run_id)
            .distinct()
        )
        return list(self.db.scalars(statement).all())

    def get_new_models_for_latest_run(self) -> list[str]:
        """Public helper used by the API endpoint."""

        latest_run = self.get_latest_collection_run()
        if latest_run is None:
            return []

        return self._detect_new_models(latest_run.id)

    def get_latest_run_records(
        self,
        source_name: str | None = None,
        license_type: str | None = None,
        new_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Return an aggregated model-level view for the latest completed run."""

        latest_run = self.get_latest_collection_run()
        if latest_run is None:
            return []

        statement = (
            select(Model, ModelMetric, Source)
            .join(ModelMetric, Model.id == ModelMetric.model_id)
            .join(Source, Source.id == ModelMetric.source_id)
            .where(ModelMetric.collection_run_id == latest_run.id)
        )

        rows = self.db.execute(statement).all()
        aggregated_records = self._aggregate_model_rows(rows)

        if source_name:
            aggregated_records = [
                record
                for record in aggregated_records
                if source_name in record["source_names"]
            ]

        if license_type:
            aggregated_records = [
                record
                for record in aggregated_records
                if (record.get("license_type") or "").lower() == license_type.lower()
            ]

        if new_only:
            latest_new_models = set(self.get_new_models_for_latest_run())
            aggregated_records = [
                record
                for record in aggregated_records
                if record["model_name"] in latest_new_models
            ]

        aggregated_records.sort(key=lambda record: record["model_name"].lower())
        return aggregated_records

    def _aggregate_model_rows(self, rows: list[tuple[Model, ModelMetric, Source]]) -> list[dict]:
        """Merge source rows into one model-level view for the latest run."""

        aggregated_by_model: dict[int, dict[str, Any]] = {}

        metric_fields = [
            "intelligence_score_raw",
            "intelligence_score_normalized",
            "input_price_per_1m_tokens_raw",
            "input_price_per_1m_tokens_normalized",
            "output_price_per_1m_tokens_raw",
            "output_price_per_1m_tokens_normalized",
            "tokens_per_second_raw",
            "tokens_per_second_normalized",
            "ttft_seconds_raw",
            "ttft_seconds_normalized",
            "context_window_raw",
            "context_window_normalized",
            "last_updated_at",
        ]

        for model, model_metric, source in rows:
            if model.id not in aggregated_by_model:
                aggregated_by_model[model.id] = {
                    "model_id": model.id,
                    "model_name": model.model_name,
                    "normalized_model_name": model.normalized_model_name,
                    "license_type": model.license_type,
                    "source_names": [source.name],
                }

            aggregated_record = aggregated_by_model[model.id]
            if source.name not in aggregated_record["source_names"]:
                aggregated_record["source_names"].append(source.name)

            for field_name in metric_fields:
                aggregated_value = aggregated_record.get(field_name)
                current_value = getattr(model_metric, field_name)
                if aggregated_value is None and current_value is not None:
                    aggregated_record[field_name] = current_value

        return list(aggregated_by_model.values())

    def clear_saved_recommendations_for_run(self, collection_run_id: int) -> None:
        """Remove previously stored recommendation results for one run."""

        statement = select(RecommendationResult).where(
            RecommendationResult.collection_run_id == collection_run_id
        )
        existing_results = self.db.scalars(statement).all()
        for result in existing_results:
            self.db.delete(result)
        self.db.commit()
