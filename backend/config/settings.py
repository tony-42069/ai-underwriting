"""
Configuration settings for the AI Underwriting system.
"""
import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "AI Underwriting Assistant"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI dev server
    ]
    
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ai_underwriting")
    
    # Document Processing Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".xlsx"]
    
    # OCR Configuration
    POPPLER_PATH: str = os.getenv(
        "POPPLER_PATH",
        r"C:\Users\dsade\Documents\poppler-24.08.0\Library\bin"  # Default Windows path
    )
    TESSERACT_PATH: str = os.getenv(
        "TESSERACT_PATH",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Default Windows path
    )
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str = os.getenv(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", ""
    )
    
    # Document Processing Settings
    MAX_CHUNK_SIZE: int = 1000  # Maximum characters per text chunk
    OVERLAP_SIZE: int = 100     # Overlap between chunks
    MIN_CONFIDENCE_SCORE: float = 0.7  # Minimum confidence score for extractions
    
    # Extraction Settings
    TENANT_CONCENTRATION_THRESHOLD: float = 20.0  # Percentage for tenant concentration warning
    MAX_EXPENSE_RATIO: float = 80.0  # Maximum normal expense ratio
    MIN_DSCR: float = 1.2  # Minimum acceptable Debt Service Coverage Ratio
    MAX_LTV: float = 75.0  # Maximum acceptable Loan to Value ratio
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File Storage Settings
    STORAGE_PROVIDER: str = "local"  # Options: local, s3
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "")
    
    # Performance Settings
    MAX_WORKERS: int = 4  # Maximum number of worker processes
    BATCH_SIZE: int = 10  # Number of documents to process in a batch
    CACHE_TTL: int = 3600  # Cache time-to-live in seconds
    
    # Cleanup Settings
    FAILED_DOCUMENT_MAX_AGE_HOURS: int = 24
    COMPLETED_DOCUMENT_MAX_AGE_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Configure logging
import logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)

# Export settings
__all__ = ["settings"]
