from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_version: str = "0.1.0"
    web_origin: str = "http://localhost:5173"
    database_url: str = "sqlite:///./content_diagnosis.db"
    analysis_provider: str = "mock"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    storage_path: Path = Path("./data")
    playwright_headless: bool = True
    max_pages_per_source: int = 20
    request_delay_ms: int = 750
    # Minimum collected pages before an entity can be treated as comparable and
    # receive a total score. A single homepage (1 page) must never qualify (rule 12).
    comparability_min_pages: int = 3

    # Async job backend: "inline" (dev, in-process thread) or "celery" (production).
    job_backend: str = "inline"
    redis_url: str | None = None

    # Storage backend: "local" filesystem (dev) or "s3" (S3-compatible, production).
    storage_backend: str = "local"
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_region: str | None = None
    s3_prefix: str = ""

    # When set, the API requires "Authorization: Bearer <token>". Unset = open (dev).
    api_auth_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
