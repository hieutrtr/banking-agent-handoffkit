"""HandoffKit REST API Module.

Contains FastAPI application and routes for AI-to-human handoff orchestration.

Example usage:
    from handoffkit.api import create_app

    app = create_app()
"""

from handoffkit.api.app import create_app, run_app
from handoffkit.api.config import get_api_settings, APISettings

__all__ = [
    "create_app",
    "run_app",
    "get_api_settings",
    "APISettings",
]
