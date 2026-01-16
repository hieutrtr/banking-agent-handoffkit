"""HandoffKit API Routes.

Contains route handlers for the REST API.
"""

from handoffkit.api.routes.handoff import router as handoff_router
from handoffkit.api.routes.health import router as health_router
from handoffkit.api.routes.check import router as check_router

__all__ = [
    "health_router",
    "handoff_router",
    "check_router",
]
