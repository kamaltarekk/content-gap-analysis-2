from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    web_origin: str = "http://localhost:5173"
    database_url: str = "sqlite:///./content_diagnosis.db"
    analysis_provider: str = "mock"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    storage_path: Path = Path("./data")
    playwright_headless: bool = True
    max_pages_per_source: int = 20
    request_delay_ms: int = 750

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
