"""FastAPI application factory for HandoffKit REST API."""

from typing import Any, Optional


def create_app(config: Optional[Any] = None) -> Any:
    """Create and configure the FastAPI application.

    Args:
        config: Optional HandoffConfig for the API.

    Returns:
        Configured FastAPI application.

    Note:
        Requires [dashboard] optional dependencies:
        pip install handoffkit[dashboard]
    """
    try:
        from fastapi import FastAPI
    except ImportError:
        raise ImportError(
            "FastAPI is required for the REST API. "
            "Install with: pip install handoffkit[dashboard]"
        )

    app = FastAPI(
        title="HandoffKit API",
        description="REST API for AI-to-human handoff orchestration",
        version="0.1.0",
    )

    # Routes will be added in future stories
    # from handoffkit.api.routes import handoff, health, config as config_routes
    # app.include_router(health.router, prefix="/api/v1")
    # app.include_router(handoff.router, prefix="/api/v1")
    # app.include_router(config_routes.router, prefix="/api/v1")

    return app
