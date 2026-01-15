"""
Application configuration settings.
"""
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=5000, description="Server port")
    ENVIRONMENT: Literal["development", "production", "staging"] = Field(
        default="development", description="Environment"
    )
    DEBUG: bool = Field(default=True, description="Debug mode")

    # Database Configuration
    DATABASE_URL: str = Field(
        ..., description="PostgreSQL database URL"
    )
    DB_POOL_SIZE: int = Field(default=20, description="Database pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Pool recycle time")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries")

    # JWT Configuration
    JWT_SECRET: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRES_IN: str = Field(default="7d", description="JWT expiration time")
    JWT_REFRESH_EXPIRES_IN: str = Field(
        default="30d", description="Refresh token expiration"
    )
    COOKIE_EXPIRES_IN: int = Field(default=7, description="Cookie expiration in days")

    # Frontend Configuration
    FRONTEND_URL: str = Field(
        default="http://localhost:3000", description="Frontend URL"
    )
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
        description="Allowed CORS origins (comma-separated)",
    )

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def parse_origins(cls, v: str) -> list[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Email Configuration
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USER: str = Field(default="", description="SMTP username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    SMTP_FROM_EMAIL: str = Field(
        default="noreply@yourapp.com", description="From email"
    )
    SMTP_FROM_NAME: str = Field(default="Auth Backend", description="From name")
    SMTP_TLS: bool = Field(default=True, description="Use TLS")
    SMTP_SSL: bool = Field(default=False, description="Use SSL")

    # OTP Configuration
    OTP_EXPIRY_MINUTES: int = Field(default=5, description="OTP expiry in minutes")
    OTP_LENGTH: int = Field(default=6, description="OTP length")

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = Field(default="", description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str = Field(
        default="", description="Google OAuth client secret"
    )
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:5000/api/auth/google/callback",
        description="Google OAuth redirect URI",
    )

    # Google Gemini AI Configuration
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(
        default=100, description="Max requests per window"
    )
    RATE_LIMIT_WINDOW_MINUTES: int = Field(
        default=15, description="Rate limit window in minutes"
    )

    # Security
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt rounds")
    COOKIE_SECURE: bool = Field(default=False, description="Secure cookie flag")
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = Field(
        default="lax", description="Cookie SameSite attribute"
    )

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    LOG_FORMAT: Literal["json", "text"] = Field(
        default="json", description="Log format"
    )


# Global settings instance
settings = Settings()
