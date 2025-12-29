"""HandoffKit REST API Module.

Contains FastAPI application and routes.
Requires [dashboard] optional dependencies.
"""

from handoffkit.api.app import create_app

__all__ = [
    "create_app",
]
