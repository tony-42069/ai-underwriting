"""
Configuration settings for the AI Underwriting system.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    PROJECT_NAME: str = "AI Underwriting Assistant"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ai_underwriting")

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".xlsx"]

    POPPLER_PATH: str = os.getenv("POPPLER_PATH", "")
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", "")

    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str = os.getenv(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", ""
    )

    MAX_CHUNK_SIZE: int = 1000
    OVERLAP_SIZE: int = 100
    MIN_CONFIDENCE_SCORE: float = 0.7

    TENANT_CONCENTRATION_THRESHOLD: float = 20.0
    MAX_EXPENSE_RATIO: float = 80.0
    MIN_DSCR: float = 1.2
    MAX_LTV: float = 75.0

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    STORAGE_PROVIDER: str = "local"
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "")

    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))

    FAILED_DOCUMENT_MAX_AGE_HOURS: int = 24
    COMPLETED_DOCUMENT_MAX_AGE_DAYS: int = 30

    @property
    def is_poppler_configured(self) -> bool:
        return bool(self.POPPLER_PATH)

    @property
    def is_tesseract_configured(self) -> bool:
        return bool(self.TESSERACT_PATH)


settings = Settings()

import logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)

__all__ = ["settings"]
