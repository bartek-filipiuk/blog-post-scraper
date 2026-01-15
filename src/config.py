"""Configuration management using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import structlog


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    database_url: str = Field(
        default="sqlite:///./blog_scraper.db",
        description="Database connection URL"
    )

    # Scraping Configuration
    max_pages_default: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Default maximum pages to scrape per job"
    )
    rate_limit_min: float = Field(
        default=2.0,
        ge=0.5,
        description="Minimum delay between requests (seconds)"
    )
    rate_limit_max: float = Field(
        default=5.0,
        ge=1.0,
        description="Maximum delay between requests (seconds)"
    )
    request_timeout: int = Field(
        default=30,
        ge=5,
        description="HTTP request timeout (seconds)"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for failed requests"
    )

    # Concurrency
    max_concurrent_jobs: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of concurrent scraping jobs"
    )

    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Server port"
    )

    # Security
    allowed_schemes: list[str] = Field(
        default=["http", "https"],
        description="Allowed URL schemes for scraping"
    )
    blocked_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0", "::1"],
        description="Blocked hostnames to prevent SSRF"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with structlog.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if log_level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog.stdlib, log_level.upper(), structlog.stdlib.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_settings() -> Settings:
    """Get application settings (singleton pattern).

    Returns:
        Settings: Application settings instance
    """
    return Settings()


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        structlog.BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


# Initialize settings and logging on module import
settings = get_settings()
configure_logging(settings.log_level)
