"""Application configuration.

This file keeps all simple project settings in one place so the rest of
the code can import them without hard-coding paths or URLs everywhere.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object for the application.

    We use pydantic-settings because it is beginner-friendly and lets us
    keep sensible defaults while still allowing environment overrides later.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LLM Monitoring System"
    app_version: str = "0.1.0"
    debug: bool = False
    request_timeout_seconds: int = 30

    # We resolve paths from the project root to keep local execution simple.
    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    reports_dir: Path = Field(default_factory=lambda: Path("reports"))
    database_file_name: str = "llm_monitor.db"

    # These URLs are placeholders for now.
    # We will confirm working endpoints when building the collectors.
    huggingface_source_url: str = "https://huggingface.co/datasets/open-llm-leaderboard/contents"
    second_source_url: str = "https://vellum.ai/llm-leaderboard"

    @property
    def resolved_data_dir(self) -> Path:
        """Return the absolute path to the data directory."""

        return self.project_root / self.data_dir

    @property
    def resolved_reports_dir(self) -> Path:
        """Return the absolute path to the reports directory."""

        return self.project_root / self.reports_dir

    @property
    def database_url(self) -> str:
        """Build the SQLAlchemy SQLite connection string.

        SQLAlchemy expects sqlite URLs in the form:
        sqlite:////absolute/path/to/file.db
        """

        database_path = self.resolved_data_dir / self.database_file_name
        return f"sqlite:///{database_path}"


settings = Settings()
