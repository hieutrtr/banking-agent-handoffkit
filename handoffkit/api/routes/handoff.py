"""Handoff endpoint for creating and managing handoffs."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status

from handoffkit.api.exceptions import (
    HandoffCreationError,
    HelpdeskIntegrationError,
)
from handoffkit.api.models.requests import ConversationMessage, CreateHandoffRequest
from handoffkit.api.models.responses import HandoffResponse, ErrorResponse
from handoffkit.core.types import ConversationContext, HandoffDecision, HandoffPriority, Message, Speaker

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Handoff"]
)


def convert_api_message_to_core(api_msg: ConversationMessage) -> Message:
    """Convert API message model to core Message type."""
    try:
        speaker_enum = Speaker(api_msg.speaker)
    except ValueError:
        speaker_enum = Speaker.USER

    return Message(
        content=api_msg.content,
        speaker=speaker_enum,
        timestamp=api_msg.timestamp or datetime.now(timezone.utc)
    )


def convert_api_context_to_core(
    conversation_id: str,
    user_id: str,
    messages: list[ConversationMessage],
    metadata: Dict[str, Any]
) -> ConversationContext:
    """Convert API request to core ConversationContext."""
    core_messages = [convert_api_message_to_core(msg) for msg in messages]

    return ConversationContext(
        conversation_id=conversation_id,
        user_id=user_id,
        messages=core_messages,
        metadata=metadata
    )


def convert_priority(priority: Optional[str]) -> HandoffPriority:
    """Convert priority string to HandoffPriority enum."""
    if not priority:
        return HandoffPriority.MEDIUM

    priority_map = {
        "LOW": HandoffPriority.LOW,
        "MEDIUM": HandoffPriority.MEDIUM,
        "HIGH": HandoffPriority.HIGH,
        "URGENT": HandoffPriority.URGENT,
        "CRITICAL": HandoffPriority.CRITICAL,
    }

    return priority_map.get(priority.upper(), HandoffPriority.MEDIUM)


@router.post(
    "/handoff",
    response_model=HandoffResponse,
    summary="Create Handoff",
    description="Create a new handoff to a human agent.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        422: {"model": ErrorResponse, "description": "Handoff creation failed"},
        502: {"model": ErrorResponse, "description": "Helpdesk integration error"}
    }
)
async def create_handoff(request: CreateHandoffRequest) -> HandoffResponse:
    """Create a new handoff to a human agent.

    This endpoint creates a new handoff based on the provided conversation
    context. It will:
    1. Create a handoff record
    2. Apply routing rules (if enabled)
    3. Create a helpdesk ticket (if configured)
    4. Return the handoff details for tracking

    Args:
        request: CreateHandoffRequest containing conversation and handoff details

    Returns:
        HandoffResponse with handoff details and ticket/assignment info
    """
    # Generate handoff ID
    handoff_id = f"ho-{uuid.uuid4().hex[:12]}"

    logger.info(
        f"Creating handoff {handoff_id} for conversation {request.conversation_id}",
        extra={
            "handoff_id": handoff_id,
            "conversation_id": request.conversation_id,
            "user_id": request.user_id,
            "priority": request.priority,
            "skip_triggers": request.skip_triggers
        }
    )

    try:
        # Convert API request to core types
        context = convert_api_context_to_core(
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            messages=request.messages,
            metadata=request.metadata or {}
        )

        # Apply context overrides if provided
        if request.context:
            context.metadata.update(request.context)

        # Create decision object
        priority = convert_priority(request.priority)
        decision = HandoffDecision(
            should_handoff=True,
            confidence=1.0,
            reason="Manual handoff requested",
            priority=priority,
            trigger_results=[]
        )

        # Skip triggers if requested
        if request.skip_triggers:
            decision.should_handoff = True
            decision.reason = "Manual handoff - triggers skipped"
            logger.info(f"Handoff {handoff_id}: triggers skipped by request")

        # Call orchestrator to create handoff
        from handoffkit import HandoffOrchestrator

        orchestrator = HandoffOrchestrator()

        # Create handoff
        result = await orchestrator.create_handoff(context, decision)

        # Extract handoff details
        ticket_id = result.ticket_id if result else None
        ticket_url = result.ticket_url if result else None
        assigned_agent = None
        assigned_queue = None
        routing_rule = None

        # Extract assignment info from metadata
        if result and result.metadata:
            assignment = result.metadata.get("routing_assignment", {})
            if assignment.get("type") == "agent":
                assigned_agent = assignment.get("agent_id")
            elif assignment.get("type") == "queue":
                assigned_queue = assignment.get("queue_name")

            routing_rule = result.metadata.get("routing_rule")

        logger.info(
            f"Handoff {handoff_id} created successfully",
            extra={
                "handoff_id": handoff_id,
                "status": result.status.value if result else "pending",
                "ticket_id": ticket_id,
                "assigned_agent": assigned_agent,
                "assigned_queue": assigned_queue,
                "routing_rule": routing_rule
            }
        )

        return HandoffResponse(
            handoff_id=handoff_id,
            status=result.status.value if result else "pending",
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            priority=priority.value,
            ticket_id=ticket_id,
            ticket_url=ticket_url,
            assigned_agent=assigned_agent,
            assigned_queue=assigned_queue,
            routing_rule=routing_rule,
            created_at=datetime.now(timezone.utc),
            metadata={}
        )

    except ImportError as e:
        logger.error(f"Import error during handoff creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service configuration error: {str(e)}"
        )
    except HelpdeskIntegrationError as e:
        logger.error(f"Helpdesk integration error for handoff {handoff_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except HandoffCreationError as e:
        logger.warning(f"Handoff creation failed for {handoff_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during handoff creation {handoff_id}: {e}",
            extra={
                "handoff_id": handoff_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during handoff creation: {str(e)}"
        )


@router.get(
    "/handoff/{handoff_id}",
    response_model=HandoffResponse,
    summary="Get Handoff Status",
    description="Get the status of an existing handoff.",
    responses={
        404: {"model": ErrorResponse, "description": "Handoff not found"}
    }
)
async def get_handoff_status(handoff_id: str) -> HandoffResponse:
    """Get the status of an existing handoff.

    This endpoint retrieves the current status of a handoff that was
    previously created via the POST /api/v1/handoff endpoint.

    Args:
        handoff_id: The unique handoff identifier

    Returns:
        HandoffResponse with current handoff status
    """
    logger.info(
        f"Getting status for handoff {handoff_id}",
        extra={"handoff_id": handoff_id}
    )

    # TODO: Implement handoff storage and retrieval
    # For now, return a placeholder response
    # This will be implemented in Story 4-4

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Handoff with ID '{handoff_id}' not found. Handoff storage will be implemented in a future update."
    )


@router.delete(
    "/handoff/{handoff_id}",
    summary="Cancel Handoff",
    description="Cancel an existing handoff.",
    responses={
        404: {"model": ErrorResponse, "description": "Handoff not found"},
        422: {"model": ErrorResponse, "description": "Cancellation failed"}
    }
)
async def cancel_handoff(handoff_id: str) -> dict:
    """Cancel an existing handoff.

    This endpoint cancels a handoff that was previously created.
    The handoff status will be updated to "cancelled".

    Args:
        handoff_id: The unique handoff identifier

    Returns:
        Confirmation of cancellation
    """
    logger.info(
        f"Cancelling handoff {handoff_id}",
        extra={"handoff_id": handoff_id}
    )

    # TODO: Implement handoff cancellation
    # This will be implemented in a future update

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Handoff with ID '{handoff_id}' not found. Handoff cancellation will be implemented in a future update."
    )
