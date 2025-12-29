"""Handoff routes for HandoffKit API."""


def get_handoff_router():
    """Get the handoff operations router.

    Returns:
        FastAPI APIRouter for handoff endpoints.
    """
    try:
        from fastapi import APIRouter
    except ImportError:
        raise ImportError(
            "FastAPI is required for the REST API. "
            "Install with: pip install handoffkit[dashboard]"
        )

    router = APIRouter(tags=["handoff"], prefix="/handoff")

    @router.post("/check")
    async def check_handoff():
        """Check if handoff is needed for a message."""
        raise NotImplementedError("Handoff check endpoint pending")

    @router.post("/")
    async def create_handoff():
        """Create a new handoff request."""
        raise NotImplementedError("Create handoff endpoint pending")

    @router.get("/{handoff_id}")
    async def get_handoff_status(handoff_id: str):
        """Get handoff status by ID."""
        raise NotImplementedError("Get handoff status endpoint pending")

    return router
