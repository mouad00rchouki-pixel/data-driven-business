"""FastAPI route definitions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Model
from app.schemas import (
    CollectionRequest,
    CollectionResponse,
    HealthResponse,
    MarkdownReportResponse,
    ModelListItem,
    NewModelsResponse,
    ProfileWeightsResponse,
    RecommendationItem,
    RecommendationResponse,
)
from app.services.collection_service import CollectionService
from app.services.recommendation_service import RecommendationService
from app.utils.report_generator import ReportGenerator
from app.utils.scoring import get_available_profiles


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Simple health endpoint."""

    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@router.post("/collect", response_model=CollectionResponse)
def collect_data(
    request: CollectionRequest,
    db: Session = Depends(get_db),
) -> CollectionResponse:
    """Run the collectors and store the result in SQLite."""

    service = CollectionService(db)

    try:
        result = service.run_collection(
            max_models_per_source=request.max_models_per_source
        )
        return CollectionResponse(**result)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Collection failed: {error}") from error


@router.get("/models", response_model=list[ModelListItem])
def list_models(
    source_name: str | None = Query(default=None),
    license_type: str | None = Query(default=None),
    new_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[ModelListItem]:
    """List the latest aggregated model rows with optional filters."""

    service = CollectionService(db)
    records = service.get_latest_run_records(
        source_name=source_name,
        license_type=license_type,
        new_only=new_only,
    )
    return [ModelListItem(**record) for record in records]


@router.get("/new-models", response_model=NewModelsResponse)
def list_new_models(db: Session = Depends(get_db)) -> NewModelsResponse:
    """Show models that are new in the latest run compared to the previous run."""

    service = CollectionService(db)
    latest_run = service.get_latest_collection_run()
    return NewModelsResponse(
        latest_run_id=latest_run.id if latest_run else None,
        new_models=service.get_new_models_for_latest_run(),
    )


@router.get("/profiles", response_model=list[ProfileWeightsResponse])
def list_profiles() -> list[ProfileWeightsResponse]:
    """Return the scoring profiles and their weights."""

    return [ProfileWeightsResponse(**profile) for profile in get_available_profiles()]


@router.get("/recommend", response_model=RecommendationResponse)
def recommend_models(
    profile: str = Query(...),
    commercial_use: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    """Recommend the top models for a given enterprise profile."""

    collection_service = CollectionService(db)
    latest_run = collection_service.get_latest_collection_run()
    if latest_run is None:
        raise HTTPException(
            status_code=404,
            detail="No completed collection run found. Call POST /collect first.",
        )

    records = collection_service.get_latest_run_records()
    recommendation_service = RecommendationService(db=db)

    try:
        recommendations = recommendation_service.recommend(
            records=records,
            profile_name=profile,
            commercial_use=commercial_use,
            top_n=3,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    model_rows = db.scalars(select(Model)).all()
    model_id_lookup = {model.model_name: model.id for model in model_rows}
    collection_service.clear_saved_recommendations_for_run(latest_run.id)
    recommendation_service.save_recommendations(
        collection_run_id=latest_run.id,
        recommendations=recommendations,
        model_id_lookup=model_id_lookup,
        commercial_use=commercial_use,
    )

    return RecommendationResponse(
        profile=profile,
        commercial_use=commercial_use,
        results=[RecommendationItem(**item) for item in recommendations],
    )


@router.get("/report/markdown", response_model=MarkdownReportResponse)
def generate_markdown_report(
    db: Session = Depends(get_db),
) -> MarkdownReportResponse:
    """Generate and save a markdown report for the latest run."""

    collection_service = CollectionService(db)
    report_generator = ReportGenerator(collection_service)

    try:
        report_data = report_generator.generate_markdown_report()
        return MarkdownReportResponse(**report_data)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate report: {error}",
        ) from error
