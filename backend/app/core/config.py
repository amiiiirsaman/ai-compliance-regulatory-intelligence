"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Compliance Intelligence System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_BASE_URL: str = "http://localhost:8000/api/v1"
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    AWS_BEDROCK_MODEL_ID: str = "amazon.nova-pro-v1:0"
    AWS_TEXTRACT_ENABLED: bool = True
    
    # S3 Configuration
    S3_BUCKET_NAME: str = "compliance-documents"
    S3_REGION: str = "us-east-1"
    S3_PRESIGNED_URL_EXPIRY: int = 3600
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Bedrock Rate Limiting
    BEDROCK_MAX_RETRIES: int = 3
    BEDROCK_RETRY_DELAY: float = 1.0
    BEDROCK_MAX_CONCURRENT_REQUESTS: int = 10
    BEDROCK_REQUEST_TIMEOUT: int = 60
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100
    
    # Document Processing
    MAX_UPLOAD_SIZE_MB: int = 50
    SUPPORTED_FILE_TYPES: str = "pdf,docx,txt"
    
    @property
    def supported_file_types_list(self) -> List[str]:
        return [ft.strip() for ft in self.SUPPORTED_FILE_TYPES.split(",")]
    
    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
