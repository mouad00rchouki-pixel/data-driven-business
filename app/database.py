"""Database connection helpers.

This file creates the SQLAlchemy engine, session factory, and initialization
helpers. Keeping these pieces together makes the rest of the code cleaner.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


# For SQLite, check_same_thread=False allows sessions to be used in FastAPI
# request handling without SQLite thread errors.
engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def init_db() -> None:
    """Create required folders and all database tables."""

    settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)

    # Import models here so SQLAlchemy knows about them before create_all.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """Yield a database session.

    FastAPI dependencies will use this generator later. The finally block
    makes sure every session is properly closed.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
