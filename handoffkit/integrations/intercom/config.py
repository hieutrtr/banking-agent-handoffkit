"""Intercom integration configuration.

Provides configuration model for Intercom API credentials.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class IntercomConfig(BaseModel):
    """Configuration for Intercom integration.

    Attributes:
        access_token: Intercom API access token (excluded from repr for security)
        app_id: Optional Intercom app ID (used for conversation URLs)

    Example:
        >>> config = IntercomConfig(
        ...     access_token="dG9rZW4...",
        ...     app_id="abc123"
        ... )

    Environment Variables:
        INTERCOM_ACCESS_TOKEN: Intercom API access token
        INTERCOM_APP_ID: Optional Intercom app ID
    """

    access_token: str = Field(
        description="Intercom API access token",
        repr=False,  # Exclude from repr for security
    )
    app_id: Optional[str] = Field(
        default=None,
        description="Optional Intercom app ID (used for conversation URLs)",
    )

    @field_validator("access_token", mode="before")
    @classmethod
    def validate_access_token(cls, v: str) -> str:
        """Validate access token is not empty."""
        if not v or not v.strip():
            raise ValueError("Access token cannot be empty")
        return v.strip()

    @field_validator("app_id", mode="before")
    @classmethod
    def validate_app_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate app_id format if provided."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        return v

    @classmethod
    def from_env(cls) -> Optional["IntercomConfig"]:
        """Create config from environment variables.

        Reads from:
        - INTERCOM_ACCESS_TOKEN (required)
        - INTERCOM_APP_ID (optional)

        Returns:
            IntercomConfig if INTERCOM_ACCESS_TOKEN is set, None otherwise.
        """
        access_token = os.environ.get("INTERCOM_ACCESS_TOKEN")
        app_id = os.environ.get("INTERCOM_APP_ID")

        if access_token:
            return cls(
                access_token=access_token,
                app_id=app_id,
            )
        return None

    def to_integration_kwargs(self) -> dict[str, Optional[str]]:
        """Convert to kwargs for IntercomIntegration constructor.

        Returns:
            Dictionary with access_token and app_id.
        """
        return {
            "access_token": self.access_token,
            "app_id": self.app_id,
        }
