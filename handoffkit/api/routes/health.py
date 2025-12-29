"""Health check route for HandoffKit API."""


def get_health_router():
    """Get the health check router.

    Returns:
        FastAPI APIRouter for health endpoints.
    """
    try:
        from fastapi import APIRouter
    except ImportError:
        raise ImportError(
            "FastAPI is required for the REST API. "
            "Install with: pip install handoffkit[dashboard]"
        )

    router = APIRouter(tags=["health"])

    @router.get("/health")
    async def health_check():
        """Check API health status."""
        return {"status": "healthy", "version": "0.1.0"}

    return router
