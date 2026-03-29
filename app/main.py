"""FastAPI entry point placeholder.

This file creates the application, initializes the database, and includes
the API routes.
"""

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.config import settings
from app.database import init_db


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A beginner-friendly LLM monitoring system.",
)


@app.on_event("startup")
def startup_event() -> None:
    """Initialize the database when the app starts."""

    init_db()


app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    """Friendly root endpoint."""

    return {"message": "LLM Monitoring System API is running."}
