"""Exception handlers and custom exceptions for HandoffKit REST API."""

import logging
import traceback
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from handoffkit.api.models.responses import ErrorResponse

# Configure logging
logger = logging.getLogger(__name__)


class HandoffKitAPIError(Exception):
    """Base exception for HandoffKit API errors."""

    def __init__(
        self,
        error: str,
        message: str,
        status_code: int = 500,
        detail: Optional[Any] = None
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class HandoffNotFoundError(HandoffKitAPIError):
    """Raised when a handoff is not found."""

    def __init__(self, handoff_id: str):
        super().__init__(
            error="handoff_not_found",
            message=f"Handoff with ID '{handoff_id}' not found",
            status_code=404,
            detail={"handoff_id": handoff_id}
        )


class ConversationNotFoundError(HandoffKitAPIError):
    """Raised when a conversation is not found."""

    def __init__(self, conversation_id: str):
        super().__init__(
            error="conversation_not_found",
            message=f"Conversation with ID '{conversation_id}' not found",
            status_code=404,
            detail={"conversation_id": conversation_id}
        )


class InvalidRequestError(HandoffKitAPIError):
    """Raised when request validation fails."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            error="invalid_request",
            message=message,
            status_code=400,
            detail=detail
        )


class HandoffCreationError(HandoffKitAPIError):
    """Raised when handoff creation fails."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            error="handoff_creation_failed",
            message=message,
            status_code=422,
            detail=detail
        )


class HandoffActionError(HandoffKitAPIError):
    """Raised when handoff action fails."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            error="handoff_action_failed",
            message=message,
            status_code=422,
            detail=detail
        )


class HelpdeskIntegrationError(HandoffKitAPIError):
    """Raised when helpdesk integration fails."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            error="helpdesk_integration_error",
            message=message,
            status_code=502,
            detail=detail
        )


class RateLimitExceededError(HandoffKitAPIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            error="rate_limit_exceeded",
            message=message,
            status_code=429,
            detail={"retry_after": 60}
        )


class AuthenticationError(HandoffKitAPIError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            error="authentication_required",
            message=message,
            status_code=401
        )


class AuthorizationError(HandoffKitAPIError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            error="access_denied",
            message=message,
            status_code=403
        )


# Request ID context
_request_id_context: Optional[str] = None


@asynccontextmanager
async def request_id_context(request_id: str) -> AsyncGenerator[None, None]:
    """Context manager for request ID."""
    global _request_id_context
    _request_id_context = request_id
    try:
        yield
    finally:
        _request_id_context = None


def get_current_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return _request_id_context


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions."""

    # Generate request ID if not present
    request_id = get_current_request_id() or getattr(request.state, "request_id", "unknown")

    # Log the exception
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )

    # Return generic error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred",
            detail=str(exc) if logger.isEnabledFor(logging.DEBUG) else None,
            request_id=request_id
        ).model_dump(mode="json")
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""

    request_id = get_current_request_id() or getattr(request.state, "request_id", "unknown")

    # Log validation errors at warning level
    logger.warning(
        f"Validation error: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": exc.errors()
        }
    )

    # Format validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            detail=errors,
            request_id=request_id
        ).model_dump(mode="json")
    )


async def handoffkit_api_error_handler(request: Request, exc: HandoffKitAPIError) -> JSONResponse:
    """Handle HandoffKit API exceptions."""

    request_id = get_current_request_id() or getattr(request.state, "request_id", "unknown")

    # Log the error
    logger.warning(
        f"API error: {exc.message}",
        extra={
            "request_id": request_id,
            "error_type": exc.error,
            "status_code": exc.status_code
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error,
            message=exc.message,
            detail=exc.detail,
            request_id=request_id
        ).model_dump(mode="json")
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Set up exception handlers for the FastAPI application."""

    # Register exception handlers
    app.add_exception_handler(HandoffKitAPIError, handoffkit_api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)