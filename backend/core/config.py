from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # Project information
    PROJECT_NAME: str = "Document Processing Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    # File upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/bmp"
    ]
    
    # Processing
    PROCESSING_TIMEOUT: int = 300  # 5 minutes
    MAX_RETRY_ATTEMPTS: int = 3
    BATCH_SIZE: int = 10
    
    # OCR Configuration
    TESSERACT_CMD: Optional[str] = None  # Set path for Windows
    OCR_LANGUAGE: str = "eng"
    OCR_CONFIG: str = "--oem 3 --psm 6"
    
    # NLP Configuration
    SPACY_MODEL: str = "en_core_web_sm"
    TRANSFORMERS_CACHE_DIR: str = "ml_models/cache"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001
    
    # Email (for password reset, etc.)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    AZURE_OCR_KEY: Optional[str] = None
    AZURE_OCR_ENDPOINT: Optional[str] = None
    
    # Development
    DEBUG: bool = False
    RELOAD: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.TRANSFORMERS_CACHE_DIR, exist_ok=True)
