"""HandoffKit API Routes.

Contains route handlers for the REST API.
"""

from handoffkit.api.routes.handoff import get_handoff_router
from handoffkit.api.routes.health import get_health_router

__all__ = [
    "get_health_router",
    "get_handoff_router",
]
