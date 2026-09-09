"""Unified environment and application settings for the Business Data Intelligence platform."""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Business Text-to-SQL Analytics Platform"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "analytics_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SCHEMA: str = "analytics"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # Read-only Execution Role credentials (if configured)
    POSTGRES_READONLY_USER: str = ""
    POSTGRES_READONLY_PASSWORD: str = ""

    # LLM Settings (Groq default)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    LLM_PROVIDER: Literal["groq", "openai", "mock"] = "groq"
    LLM_TEMPERATURE: float = 0.0
    LLM_TIMEOUT_SECONDS: float = 30.0

    # Embeddings & Vector Store
    EMBEDDING_PROVIDER: Literal["local", "groq", "fastembed"] = "local"
    EMBEDDING_DIMENSION: int = 384
    VECTOR_SIMILARITY_THRESHOLD: float = 0.45

    # Auth & Sessions
    AUTH_MODE: Literal["development", "oauth"] = "development"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    SESSION_SECRET: str = "development-insecure-secret-key-replace-in-production"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "Lax"

    # Development-only identity fallback
    DEV_USER_EMAIL: str = "dev@example.com"
    DEV_USER_NAME: str = "Local Developer"
    LOCAL_TENANT_ID: str = "default"

    # Ingestion Limits
    MAX_CSV_BYTES: int = 50 * 1024 * 1024  # 50 MB
    MAX_BATCH_ROWS: int = 2000

    # SQL Execution Safety
    SQL_TIMEOUT_SECONDS: float = 15.0
    SQL_MAX_ROWS: int = 1000

    # Confidence Thresholds
    CONFIDENCE_AUTO_EXECUTE: float = 0.85
    CONFIDENCE_CLARIFICATION_REQUIRED: float = 0.60

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def readonly_database_url(self) -> str:
        user = self.POSTGRES_READONLY_USER or self.POSTGRES_USER
        password = self.POSTGRES_READONLY_PASSWORD or self.POSTGRES_PASSWORD
        return (
            f"postgresql+psycopg://{user}:{password}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
