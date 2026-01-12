"""Request and response models for HandoffKit REST API."""

from handoffkit.api.models.requests import (
    CheckHandoffRequest,
    ConversationMessage,
    CreateHandoffRequest,
    HandoffActionRequest,
)

from handoffkit.api.models.responses import (
    CheckResult,
    ErrorResponse,
    HandoffResponse,
    HandoffStatusResponse,
    HealthStatus,
    PaginatedResponse,
    PaginationParams,
)

__all__ = [
    # Requests
    "CheckHandoffRequest",
    "ConversationMessage",
    "CreateHandoffRequest",
    "HandoffActionRequest",
    # Responses
    "CheckResult",
    "ErrorResponse",
    "HandoffResponse",
    "HandoffStatusResponse",
    "HealthStatus",
    "PaginatedResponse",
    "PaginationParams",
]