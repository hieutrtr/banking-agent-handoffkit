"""FastAPI application factory and entry point for HandoffKit REST API."""

import logging
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

# Configure logging before importing other modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

try:
    from fastapi import FastAPI, Request, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except ImportError:
    raise ImportError(
        "FastAPI is required for the REST API. "
        "Install with: pip install handoffkit[dashboard]"
    )

from handoffkit.api.config import get_api_settings, validate_api_settings
from handoffkit.api.exceptions import setup_exception_handlers
from handoffkit.api.models.responses import HealthStatus
from handoffkit.api.routes.health import router as health_router
from handoffkit.api.routes.check import router as check_router
from handoffkit.api.routes.handoff import router as handoff_router


# Configure logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""

    # Startup
    logger.info("Starting HandoffKit API...")

    # Load and validate settings
    settings = get_api_settings()
    warnings = validate_api_settings(settings)

    for warning in warnings:
        logger.warning(warning)

    # Log startup information
    logger.info(
        f"HandoffKit API starting on {settings.host}:{settings.port}",
        extra={
            "host": settings.host,
            "port": settings.port,
            "debug": settings.debug,
            "workers": settings.workers
        }
    )

    yield

    # Shutdown
    logger.info("Shutting down HandoffKit API...")


def create_app(config: Optional[Any] = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config: Optional settings for the API.

    Returns:
        Configured FastAPI application.

    Note:
        Requires [dashboard] optional dependencies:
        pip install handoffkit[dashboard]
    """
    # Get settings
    settings = get_api_settings()

    # Create FastAPI application
    app = FastAPI(
        title="HandoffKit API",
        description="""
## AI-to-Human Handoff Orchestration API

This API provides endpoints for managing AI-to-human handoff operations,
including conversation monitoring, handoff creation, and status tracking.

### Features
- **Handoff Detection**: Check if a conversation should be handed off to a human
- **Handoff Creation**: Create and manage handoffs to human agents
- **Status Tracking**: Track handoff status and resolution
- **Health Monitoring**: Monitor API and component health

### Getting Started
- Check `/api/v1/health` for API health status
- See `/docs` for detailed API documentation
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next) -> JSONResponse:
        """Add request ID to all requests."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store request ID in request state
        request.state.request_id = request_id

        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

    # Request timing middleware
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next) -> JSONResponse:
        """Add timing information to requests."""
        start_time = datetime.utcnow()

        response = await call_next(request)

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Log slow requests
        if duration > 1000:  # Log requests taking more than 1 second
            logger.warning(
                f"Slow request: {request.url.path} - {duration:.2f}ms",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": duration,
                    "status_code": response.status_code
                }
            )

        return response

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include health check router
    app.include_router(health_router)

    # Include check router
    app.include_router(check_router)

    # Include handoff router
    app.include_router(handoff_router)

    # Root endpoint
    @app.get(
        "/",
        tags=["Root"],
        summary="API Root",
        description="Root endpoint with API information"
    )
    async def root() -> dict:
        """Return API information."""
        return {
            "name": "HandoffKit API",
            "version": "1.0.0",
            "description": "AI-to-Human Handoff Orchestration API",
            "docs": "/docs",
            "health": "/api/v1/health"
        }

    # Global exception handler for unhandled errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(
            f"Unhandled exception: {exc}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "error": str(exc)
            }
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "request_id": request_id
            }
        )

    return app


# Convenience function to run the app
def run_app() -> None:
    """Run the FastAPI application with uvicorn."""
    import uvicorn

    settings = get_api_settings()

    uvicorn.run(
        "handoffkit.api.app:create_app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=1 if settings.is_development else settings.workers,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_app()