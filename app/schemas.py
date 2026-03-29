"""Pydantic schemas for API input and output.

These classes define the shape of the data our API returns. Keeping them
separate from database models avoids mixing storage logic with API logic.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Simple response for the health endpoint."""

    status: str
    app_name: str
    version: str


class SourceResponse(BaseModel):
    """Represents one source in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str | None = None
    source_type: str | None = None
    last_collected_at: datetime | None = None


class CollectionRunResponse(BaseModel):
    """Represents a collection run."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    notes: str | None = None


class CollectionRequest(BaseModel):
    """Request body for triggering a collection."""

    max_models_per_source: int = Field(
        default=25,
        ge=5,
        le=200,
        description="How many models to request from each source.",
    )


class CollectionResponse(BaseModel):
    """Summary returned after a collection run."""

    collection_run_id: int
    status: str
    source_record_count: int
    merged_record_count: int
    new_model_count: int
    new_models: list[str]


class ModelResponse(BaseModel):
    """Basic model information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    model_name: str
    normalized_model_name: str
    license_type: str | None = None
    first_seen_run_id: int | None = None
    created_at: datetime


class ModelListItem(BaseModel):
    """Aggregated latest-run model view used by listing endpoints."""

    model_id: int
    model_name: str
    normalized_model_name: str
    license_type: str | None = None
    source_names: list[str]

    intelligence_score_raw: float | None = None
    intelligence_score_normalized: float | None = None
    input_price_per_1m_tokens_raw: float | None = None
    input_price_per_1m_tokens_normalized: float | None = None
    output_price_per_1m_tokens_raw: float | None = None
    output_price_per_1m_tokens_normalized: float | None = None
    tokens_per_second_raw: float | None = None
    tokens_per_second_normalized: float | None = None
    ttft_seconds_raw: float | None = None
    ttft_seconds_normalized: float | None = None
    context_window_raw: float | None = None
    context_window_normalized: float | None = None
    last_updated_at: datetime | None = None


class ModelMetricResponse(BaseModel):
    """A stored metrics row for one model, one source, and one run."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    collection_run_id: int
    model_id: int
    source_id: int
    raw_model_name: str

    intelligence_score_raw: float | None = None
    intelligence_score_normalized: float | None = None

    input_price_per_1m_tokens_raw: float | None = None
    input_price_per_1m_tokens_normalized: float | None = None

    output_price_per_1m_tokens_raw: float | None = None
    output_price_per_1m_tokens_normalized: float | None = None

    tokens_per_second_raw: float | None = None
    tokens_per_second_normalized: float | None = None

    ttft_seconds_raw: float | None = None
    ttft_seconds_normalized: float | None = None

    context_window_raw: float | None = None
    context_window_normalized: float | None = None

    license_type_raw: str | None = None
    last_updated_at: datetime | None = None
    collected_at: datetime


class RecommendQueryParams(BaseModel):
    """Validated query parameters for the recommendation endpoint."""

    profile: str = Field(..., description="Enterprise profile name")
    commercial_use: bool = Field(
        default=False,
        description="If true, exclude models with restrictive or unclear licenses.",
    )


class RecommendationItem(BaseModel):
    """One recommended model in the final API response."""

    rank: int
    model_name: str
    profile_name: str
    profile_score: float
    license_type: str | None = None
    source_names: list[str] = []
    justification: str


class RecommendationResponse(BaseModel):
    """Top recommendations for a profile."""

    profile: str
    commercial_use: bool
    results: list[RecommendationItem]


class NewModelsResponse(BaseModel):
    """Response for the new-model detection endpoint."""

    latest_run_id: int | None = None
    new_models: list[str]


class ProfileWeightsResponse(BaseModel):
    """Describes one available scoring profile."""

    profile_name: str
    description: str
    weights: dict[str, float]


class ReportSummaryResponse(BaseModel):
    """Simple response for generated reports."""

    generated_at: datetime
    report_path: str
    title: str


class MarkdownReportResponse(BaseModel):
    """Response for the markdown report endpoint."""

    title: str
    generated_at: str
    report_path: str
    content: str
