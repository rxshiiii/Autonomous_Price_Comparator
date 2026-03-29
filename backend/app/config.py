"""
Application configuration management using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://pricecomp:pricecomp123@localhost:5432/pricecomparator",
        description="PostgreSQL database URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    REDIS_CACHE_TTL: int = Field(default=3600, description="Default cache TTL in seconds")

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery result backend")

    # JWT Authentication
    SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production-minimum-32-characters",
        description="Secret key for JWT"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiry")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry")

    # GROQ API
    GROQ_API_KEY: str = Field(default="", description="GROQ API key")
    GROQ_MODEL: str = Field(default="llama-3.1-70b-versatile", description="GROQ model name")

    # Web Scraping
    PROXY_URL: str = Field(default="", description="Proxy URL for scraping")
    USER_AGENT_POOL_SIZE: int = Field(default=50, description="User agent pool size")
    MAX_CONCURRENT_SCRAPES: int = Field(default=5, description="Max concurrent scraping jobs")

    # Email (optional)
    SENDGRID_API_KEY: str = Field(default="", description="SendGrid API key")
    FROM_EMAIL: str = Field(default="noreply@pricecomparator.com", description="From email address")

    # Monitoring (optional)
    SENTRY_DSN: str = Field(default="", description="Sentry DSN for error tracking")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment name")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
