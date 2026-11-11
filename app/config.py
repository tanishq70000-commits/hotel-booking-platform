"""Application configuration using Pydantic Settings v2."""

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Info
    APP_NAME: str = "Hotel Reservation API"
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    VERSION: str = Field(default="1.0.0", alias="APP_VERSION")
    COMMIT_SHA: str = Field(default="dev-local", alias="COMMIT_SHA")
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration
    DB_HOST: str = Field(default="localhost", alias="DB_HOST")
    DB_PORT: int = Field(default=5432, alias="DB_PORT")
    DB_USER: str = Field(default="postgres", alias="DB_USER")
    DB_PASSWORD: str | None = Field(default=None, alias="DB_PASSWORD")
    DB_PASSWORD_FILE: str | None = Field(default=None, alias="DB_PASSWORD_FILE")
    DB_NAME: str = Field(default="hotel_booking", alias="DB_NAME")
    DATABASE_URL: str | None = Field(default=None, alias="DATABASE_URL")

    # DB Connection Pool Settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30

    @property
    def effective_db_password(self) -> str:
        """Resolve database password from DB_PASSWORD or DB_PASSWORD_FILE (Docker secret)."""
        if self.DB_PASSWORD:
            return self.DB_PASSWORD
        if self.DB_PASSWORD_FILE and os.path.exists(self.DB_PASSWORD_FILE):
            with open(self.DB_PASSWORD_FILE, encoding="utf-8") as f:
                return f.read().strip()
        return "postgres"

    @property
    def sync_database_url(self) -> str:
        """Return synchronous database connection URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        password = self.effective_db_password
        return f"postgresql+psycopg://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
