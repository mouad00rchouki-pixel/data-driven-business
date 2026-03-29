"""Dashboard service.

This service prepares dashboard-friendly data so the Streamlit file can stay
focused on the user interface instead of database details.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source
from app.services.collection_service import CollectionService
from app.services.recommendation_service import RecommendationService
from app.utils.scoring import get_available_profiles


class DashboardService:
    """Prepare data structures used by the Streamlit dashboard."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.collection_service = CollectionService(db)
        self.recommendation_service = RecommendationService()

    def get_dashboard_summary(self) -> dict:
        """Return top-level summary numbers for the latest run."""

        latest_run = self.collection_service.get_latest_collection_run()
        records = self.collection_service.get_latest_run_records()
        new_models = self.collection_service.get_new_models_for_latest_run()
        source_names = self.get_source_names()

        return {
            "latest_run_id": latest_run.id if latest_run else None,
            "total_models": len(records),
            "new_models_count": len(new_models),
            "source_count": len(source_names),
            "sources": source_names,
        }

    def get_source_names(self) -> list[str]:
        """Return available source names from the database."""

        statement = select(Source.name).order_by(Source.name.asc())
        return list(self.db.scalars(statement).all())

    def get_license_types(self) -> list[str]:
        """Return distinct non-empty license values from the latest run."""

        records = self.collection_service.get_latest_run_records()
        licenses = sorted(
            {
                record["license_type"]
                for record in records
                if record.get("license_type")
            }
        )
        return licenses

    def get_models_dataframe(
        self,
        source_name: str | None = None,
        license_type: str | None = None,
        new_only: bool = False,
        selected_profile: str | None = None,
        commercial_use: bool = False,
    ) -> pd.DataFrame:
        """Return a pandas DataFrame ready for display and charts."""

        records = self.collection_service.get_latest_run_records(
            source_name=source_name,
            license_type=license_type,
            new_only=new_only,
        )

        if not records:
            return pd.DataFrame()

        prepared_records = self.recommendation_service.prepare_records(records)
        dataframe = pd.DataFrame(prepared_records)

        if commercial_use:
            dataframe = dataframe[dataframe["license_type"].notna()].copy()

        if selected_profile:
            score_column = f"{selected_profile}_score"
            if score_column in dataframe.columns:
                dataframe = dataframe.sort_values(by=score_column, ascending=False)

        return dataframe

    def get_top_models_for_profile(
        self,
        profile_name: str,
        top_n: int = 5,
        commercial_use: bool = False,
    ) -> list[dict]:
        """Return top ranked recommendations for the selected profile."""

        records = self.collection_service.get_latest_run_records()
        if not records:
            return []

        return self.recommendation_service.recommend(
            records=records,
            profile_name=profile_name,
            commercial_use=commercial_use,
            top_n=top_n,
        )

    def get_new_models(self) -> list[str]:
        """Return new models from the latest run."""

        return self.collection_service.get_new_models_for_latest_run()

    def get_profile_options(self) -> list[str]:
        """Return available profile names."""

        return [profile["profile_name"] for profile in get_available_profiles()]
