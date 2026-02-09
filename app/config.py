from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://sanad_user:changeme@localhost:5432/sanad_db"
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    
    # Storage
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    STORAGE_PATH: str = "/var/sanad/audits"
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Cache TTLs (seconds)
    CACHE_TTL_DASHBOARD: int = 300  # 5 minutes
    CACHE_TTL_AUDIT: int = 3600  # 1 hour
    CACHE_TTL_ANALYTICS: int = 600  # 10 minutes
    CACHE_TTL_LIST: int = 60  # 1 minute
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra env vars that aren't in Settings


settings = Settings()
