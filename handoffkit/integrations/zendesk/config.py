"""Zendesk integration configuration.

Provides configuration model for Zendesk API credentials.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ZendeskConfig(BaseModel):
    """Configuration for Zendesk integration.

    Attributes:
        subdomain: Zendesk subdomain (e.g., 'company' for company.zendesk.com)
        email: Admin email for API access
        api_token: Zendesk API token (excluded from repr for security)

    Example:
        >>> config = ZendeskConfig(
        ...     subdomain="mycompany",
        ...     email="admin@mycompany.com",
        ...     api_token="secret-token"
        ... )

    Environment Variables:
        ZENDESK_SUBDOMAIN: Zendesk subdomain
        ZENDESK_EMAIL: Admin email
        ZENDESK_API_TOKEN: API token
    """

    subdomain: str = Field(
        description="Zendesk subdomain (e.g., 'company' for company.zendesk.com)"
    )
    email: str = Field(description="Admin email for API access")
    api_token: str = Field(
        description="Zendesk API token",
        repr=False,  # Exclude from repr for security
    )

    @field_validator("subdomain", mode="before")
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        """Validate subdomain format."""
        if not v or not v.strip():
            raise ValueError("Subdomain cannot be empty")
        # Remove any URL parts if accidentally included
        v = v.strip()
        if ".zendesk.com" in v:
            v = v.replace(".zendesk.com", "").replace("https://", "").replace("/", "")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip()

    @field_validator("api_token", mode="before")
    @classmethod
    def validate_api_token(cls, v: str) -> str:
        """Validate API token is not empty."""
        if not v or not v.strip():
            raise ValueError("API token cannot be empty")
        return v.strip()

    @classmethod
    def from_env(cls) -> Optional["ZendeskConfig"]:
        """Create config from environment variables.

        Reads from:
        - ZENDESK_SUBDOMAIN
        - ZENDESK_EMAIL
        - ZENDESK_API_TOKEN

        Returns:
            ZendeskConfig if all env vars are set, None otherwise.
        """
        subdomain = os.environ.get("ZENDESK_SUBDOMAIN")
        email = os.environ.get("ZENDESK_EMAIL")
        api_token = os.environ.get("ZENDESK_API_TOKEN")

        if all([subdomain, email, api_token]):
            return cls(
                subdomain=subdomain,  # type: ignore
                email=email,  # type: ignore
                api_token=api_token,  # type: ignore
            )
        return None

    def to_integration_kwargs(self) -> dict[str, str]:
        """Convert to kwargs for ZendeskIntegration constructor.

        Returns:
            Dictionary with subdomain, email, api_token.
        """
        return {
            "subdomain": self.subdomain,
            "email": self.email,
            "api_token": self.api_token,
        }
