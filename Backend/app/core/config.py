
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]

DEFAULT_DATABASE_URL = (
    f"sqlite:///{BACKEND_DIR / 'smartsearch.db'}"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="SMARTSEARCH_",
        extra="ignore",
    )

    app_name: str = "SmartSearch API"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = DEFAULT_DATABASE_URL


settings = Settings()
