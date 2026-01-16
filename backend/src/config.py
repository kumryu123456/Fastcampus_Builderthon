"""
Configuration management for PathPilot.

Constitution Compliance:
- Principle III: User Data Privacy - All secrets loaded from environment variables
- Principle II: API Resilience - Configurable retry and timeout settings
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    app_debug: bool = Field(default=True, description="Debug mode")
    app_secret_key: str = Field(..., description="Secret key for sessions")

    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    # AI Models - Gemini
    google_api_key: str = Field(..., description="Google Gemini API key")
    preferred_ai_model: str = Field(
        default="gemini-1.5-pro",
        description="Gemini model: gemini-1.5-pro, gemini-1.5-flash, gemini-1.0-pro",
    )

    # ElevenLabs Voice
    elevenlabs_api_key: Optional[str] = Field(default=None, description="ElevenLabs API key (optional for MVP)")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # File Upload
    max_upload_size_mb: int = Field(default=5, description="Max file upload size in MB")
    upload_dir: str = Field(default="./uploads", description="Upload directory path")

    # Logging
    log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")

    # API Rate Limiting (Constitution II: API Resilience)
    gemini_max_retries: int = Field(default=3, description="Max retry attempts for Gemini API")
    gemini_timeout_seconds: int = Field(default=30, description="Timeout for Gemini API calls")
    elevenlabs_max_retries: int = Field(default=3, description="Max retry attempts for ElevenLabs API")
    elevenlabs_timeout_seconds: int = Field(default=10, description="Timeout for ElevenLabs API calls")

    # Feature Flags (Hackathon MVP)
    feature_job_discovery: bool = Field(default=False, description="Enable job discovery agent (P2)")
    feature_mock_interview: bool = Field(default=False, description="Enable mock interview (P2)")
    feature_dashboard_stats: bool = Field(default=False, description="Enable dashboard stats (P3)")

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("app_env")
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"app_env must be one of {valid_envs}")
        return v

    @validator("preferred_ai_model")
    def validate_ai_model(cls, v):
        """Validate AI model selection."""
        valid_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]
        if v not in valid_models:
            raise ValueError(f"preferred_ai_model must be one of {valid_models}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env == "development"

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
