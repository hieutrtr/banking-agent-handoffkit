"""Configuration management for HandoffKit REST API."""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """Settings for the HandoffKit REST API."""

    model_config = SettingsConfigDict(
        env_prefix="HANDOFFKIT_API_",
        env_file=".env",
        extra="ignore",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, ge=1, le=65535, description="API server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    workers: int = Field(default=1, ge=1, le=16, description="Number of worker processes")

    # CORS settings
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Request settings
    request_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    max_request_size: int = Field(
        default=1048576,
        ge=1024,
        description="Maximum request size in bytes (1MB default)"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        json_schema_extra={"enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]}
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=100,
        ge=1,
        description="Rate limit requests per minute"
    )
    burst_allowance: int = Field(
        default=10,
        ge=1,
        description="Burst allowance for rate limiting"
    )

    # HandoffKit core settings
    default_priority: str = Field(
        default="MEDIUM",
        description="Default handoff priority"
    )
    enable_routing_rules: bool = Field(
        default=True,
        description="Enable rule-based routing"
    )

    # Helpdesk integration (can be overridden by environment)
    helpdesk_provider: Optional[str] = Field(
        default=None,
        description="Default helpdesk provider"
    )
    helpdesk_api_key: Optional[str] = Field(
        default=None,
        description="Helpdesk API key (sensitive)"
    )
    helpdesk_subdomain: Optional[str] = Field(
        default=None,
        description="Helpdesk subdomain"
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug or "localhost" in self.host

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from string if needed."""
        if isinstance(self.cors_origins, str):
            # Handle comma-separated string
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins


@lru_cache()
def get_api_settings() -> APISettings:
    """Get API settings instance (cached)."""
    return APISettings()


def validate_api_settings(settings: APISettings) -> List[str]:
    """Validate API settings and return list of warnings.

    Returns:
        List of warning messages (empty if no warnings).
    """
    warnings = []

    # Check for required settings
    if not settings.helpdesk_provider:
        warnings.append("HANDOFFKIT_API_HELPDESK_PROVIDER not set - some features may not work")

    if not settings.helpdesk_api_key:
        warnings.append("HANDOFFKIT_API_HELPDESK_API_KEY not set - helpdesk integration disabled")

    # Check for insecure configurations
    if settings.debug and not settings.is_development:
        warnings.append("Debug mode enabled in production - consider disabling")

    if "*" in settings.cors_origins:
        warnings.append("Wildcard CORS origin (*) is insecure - consider restricting")

    return warnings