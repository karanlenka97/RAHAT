"""Application configuration and environment settings."""
import logging
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Core application settings loaded from environment variables or .env file."""

    # Project metadata
    PROJECT_NAME: str = "RAHAT - Rural Assistance & Healthcare Access Tele-network"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & JWT Authentication
    JWT_SECRET: str = "rahat-dev-insecure-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration (PostgreSQL + PostGIS)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "rahat_db"
    DATABASE_URL: str | None = None

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Referral Assistant Configuration
    AI_PROVIDER: str = "mock"  # "mock", "gemini", "openai"
    AI_MODEL: str = "gemini-1.5-flash"
    AI_API_KEY: str | None = None
    AI_TIMEOUT_SECONDS: int = 15
    AI_RATE_LIMIT_PER_MINUTE: int = 30

    # Production Server Configuration
    UVICORN_WORKERS: int = 2
    RUN_DB_SEED: bool = False

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforce strict security validation when running in production mode."""
        if self.ENVIRONMENT.lower() == "production":
            if self.DEBUG:
                logger.warning("Overriding DEBUG to False for production environment.")
                object.__setattr__(self, "DEBUG", False)

            insecure_secret = "rahat-dev-insecure-secret-key-change-in-production-2026"
            if self.JWT_SECRET == insecure_secret or len(self.JWT_SECRET) < 32:
                raise ValueError(
                    "Production Security Error: A strong, unique JWT_SECRET of at least 32 characters "
                    "must be configured via the JWT_SECRET environment variable."
                )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
