"""Database table definitions.

These models describe how data is stored in SQLite. We keep the schema
explicit and easy to explain: collection runs, sources, models, metrics,
and optional saved recommendation results.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CollectionRun(Base):
    """Represents one full collection execution."""

    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="started", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    metrics: Mapped[list["ModelMetric"]] = relationship(
        back_populates="collection_run", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["RecommendationResult"]] = relationship(
        back_populates="collection_run", cascade="all, delete-orphan"
    )


class Source(Base):
    """Stores metadata about each data source."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    metrics: Mapped[list["ModelMetric"]] = relationship(back_populates="source")


class Model(Base):
    """Master table of unique LLM models."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    normalized_model_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    license_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_seen_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("collection_runs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    metrics: Mapped[list["ModelMetric"]] = relationship(back_populates="model")
    recommendations: Mapped[list["RecommendationResult"]] = relationship(
        back_populates="model"
    )


class ModelMetric(Base):
    """Stores raw and normalized metrics for a model in one collection run."""

    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("collection_runs.id"), nullable=False
    )
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)

    raw_model_name: Mapped[str] = mapped_column(String(255), nullable=False)

    intelligence_score_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    intelligence_score_normalized: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    input_price_per_1m_tokens_raw: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    input_price_per_1m_tokens_normalized: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    output_price_per_1m_tokens_raw: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    output_price_per_1m_tokens_normalized: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    tokens_per_second_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_per_second_normalized: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    ttft_seconds_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    ttft_seconds_normalized: Mapped[float | None] = mapped_column(Float, nullable=True)

    context_window_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_window_normalized: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    license_type_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    collection_run: Mapped["CollectionRun"] = relationship(back_populates="metrics")
    model: Mapped["Model"] = relationship(back_populates="metrics")
    source: Mapped["Source"] = relationship(back_populates="metrics")


class RecommendationResult(Base):
    """Optional table to store generated recommendation results."""

    __tablename__ = "recommendation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("collection_runs.id"), nullable=False
    )
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    profile_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    commercial_use: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    profile_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    justification_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    collection_run: Mapped["CollectionRun"] = relationship(
        back_populates="recommendations"
    )
    model: Mapped["Model"] = relationship(back_populates="recommendations")
