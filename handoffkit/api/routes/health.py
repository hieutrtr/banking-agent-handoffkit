"""Health check endpoints for HandoffKit REST API."""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, status

from handoffkit.api.models.responses import HealthStatus
from handoffkit.api.config import get_api_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Health"]
)

# Component status cache
_component_status: Dict[str, Any] = {}


def check_orchestrator_health() -> Dict[str, Any]:
    """Check the health of the HandoffOrchestrator."""
    try:
        # Import here to avoid circular imports
        from handoffkit import HandoffOrchestrator

        # Try to create or get orchestrator instance
        orchestrator = HandoffOrchestrator()
        if orchestrator:
            return {
                "status": "healthy",
                "message": "Orchestrator is available"
            }
        return {
            "status": "unhealthy",
            "message": "Orchestrator not initialized"
        }
    except ImportError as e:
        return {
            "status": "unavailable",
            "message": f"Import error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }


def check_helpdesk_health() -> Dict[str, Any]:
    """Check the health of the helpdesk integration."""
    try:
        from handoffkit import HandoffOrchestrator

        orchestrator = HandoffOrchestrator()
        helpdesk = orchestrator.helpdesk

        if helpdesk:
            return {
                "status": "healthy",
                "provider": helpdesk.integration_name
            }
        return {
            "status": "unavailable",
            "message": "No helpdesk configured"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }


def check_routing_health() -> Dict[str, Any]:
    """Check the health of the routing engine."""
    try:
        from handoffkit.routing import RoutingEngine, RoutingConfig

        # Try to create a routing engine
        config = RoutingConfig()
        engine = RoutingEngine(config)

        return {
            "status": "healthy",
            "message": "Routing engine is available"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Health Check",
    description="Check the health status of the HandoffKit API and its components."
)
async def health_check() -> HealthStatus:
    """Perform a health check of the API and its dependencies.

    Returns:
        HealthStatus: Overall health status and component details.
    """
    global _component_status

    settings = get_api_settings()

    # Collect component status
    components = {}

    # Check core components
    try:
        components["orchestrator"] = check_orchestrator_health()
    except Exception as e:
        components["orchestrator"] = {"status": "error", "message": str(e)}

    try:
        components["helpdesk"] = check_helpdesk_health()
    except Exception as e:
        components["helpdesk"] = {"status": "error", "message": str(e)}

    try:
        components["routing"] = check_routing_health()
    except Exception as e:
        components["routing"] = {"status": "error", "message": str(e)}

    # Determine overall status
    component_statuses = [c.get("status") for c in components.values()]
    if "error" in component_statuses:
        overall_status = "unhealthy"
    elif "unhealthy" in component_statuses or "unavailable" in component_statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    # Log health check
    logger.info(
        f"Health check: {overall_status}",
        extra={"components": components}
    )

    _component_status = {
        "status": overall_status,
        "components": components,
        "timestamp": datetime.utcnow()
    }

    return HealthStatus(
        status=overall_status,
        version="1.0.0",
        components=components
    )


@router.get(
    "/health/live",
    summary="Liveness Probe",
    description="Simple liveness probe for Kubernetes/container orchestration."
)
async def liveness_probe() -> Dict[str, str]:
    """Simple liveness probe that always returns OK.

    This endpoint is meant for container orchestration systems
    (Kubernetes, Docker) to check if the application is running.

    Returns:
        Dict: Simple status response.
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness Probe",
    description="Readiness probe that checks if the API is ready to accept traffic."
)
async def readiness_probe() -> Dict[str, Any]:
    """Readiness probe that checks if the API is ready to accept traffic.

    This endpoint is meant for container orchestration systems
    to check if the application is ready to receive requests.

    Returns:
        Dict: Readiness status and component details.
    """
    # Check if critical components are ready
    try:
        from handoffkit import HandoffOrchestrator
        orchestrator = HandoffOrchestrator()

        # If we can get the orchestrator, we're ready
        return {
            "ready": True,
            "message": "All components ready"
        }
    except Exception as e:
        return {
            "ready": False,
            "message": str(e)
        }


def get_cached_health_status() -> Dict[str, Any]:
    """Get the cached health status (if available)."""
    return _component_status or {"status": "unknown", "components": {}}