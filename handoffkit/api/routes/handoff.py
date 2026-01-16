"""Handoff endpoint for creating and managing handoffs."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends

from handoffkit.api.auth import get_api_key
from handoffkit.api.models.auth import APIKey
from handoffkit.api.exceptions import (
    HandoffCreationError,
    HelpdeskIntegrationError,
)
from handoffkit.api.models.requests import ConversationMessage, CreateHandoffRequest
from handoffkit.api.models.responses import HandoffResponse, HandoffStatusResponse, ErrorResponse
from handoffkit.core.types import ConversationContext, HandoffDecision, HandoffPriority, Message, Speaker
from handoffkit.storage import get_handoff_storage

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
async def create_handoff(
    request: CreateHandoffRequest,
    api_key: APIKey = Depends(get_api_key)
) -> HandoffResponse:
    """Create a new handoff to a human agent.

    This endpoint creates a new handoff based on the provided conversation
    context. It will:
    1. Create a handoff record
    2. Apply routing rules (if enabled)
    3. Create a helpdesk ticket (if configured)
    4. Store the handoff for status tracking
    5. Return the handoff details for tracking

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
        handoff_status = result.status.value if result else "pending"
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

        created_at = datetime.now(timezone.utc)

        logger.info(
            f"Handoff {handoff_id} created successfully",
            extra={
                "handoff_id": handoff_id,
                "status": handoff_status,
                "ticket_id": ticket_id,
                "assigned_agent": assigned_agent,
                "assigned_queue": assigned_queue,
                "routing_rule": routing_rule
            }
        )

        # Store handoff for status tracking
        try:
            storage = get_handoff_storage()
            await storage.save(handoff_id, {
                "handoff_id": handoff_id,
                "conversation_id": request.conversation_id,
                "user_id": request.user_id,
                "priority": priority.value,
                "status": handoff_status,
                "ticket_id": ticket_id,
                "ticket_url": ticket_url,
                "assigned_agent": assigned_agent,
                "assigned_queue": assigned_queue,
                "routing_rule": routing_rule,
                "metadata": request.metadata or {},
                "history": [
                    {
                        "status": handoff_status,
                        "timestamp": created_at.isoformat()
                    }
                ]
            })
            logger.info(f"Handoff {handoff_id} stored for status tracking")
        except Exception as storage_error:
            logger.warning(
                f"Failed to store handoff {handoff_id}: {storage_error}",
                extra={"handoff_id": handoff_id}
            )
            # Don't fail the handoff creation if storage fails

        return HandoffResponse(
            handoff_id=handoff_id,
            status=handoff_status,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            priority=priority.value,
            ticket_id=ticket_id,
            ticket_url=ticket_url,
            assigned_agent=assigned_agent,
            assigned_queue=assigned_queue,
            routing_rule=routing_rule,
            created_at=created_at,
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
    response_model=HandoffStatusResponse,
    summary="Get Handoff Status",
    description="Get the status of an existing handoff.",
    responses={
        404: {"model": ErrorResponse, "description": "Handoff not found"}
    }
)
async def get_handoff_status(
    handoff_id: str,
    api_key: APIKey = Depends(get_api_key)
) -> HandoffStatusResponse:
    """Get the status of an existing handoff.

    This endpoint retrieves the current status of a handoff that was
    previously created via the POST /api/v1/handoff endpoint.

    Args:
        handoff_id: The unique handoff identifier

    Returns:
        HandoffStatusResponse with current handoff status
    """
    logger.info(
        f"Getting status for handoff {handoff_id}",
        extra={"handoff_id": handoff_id}
    )

    try:
        # Get handoff from storage
        storage = get_handoff_storage()
        data = await storage.get(handoff_id)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Handoff with ID '{handoff_id}' not found"
            )

        # Build history
        history = data.get("history", [])

        # Handle created_at
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        # Handle updated_at
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return HandoffStatusResponse(
            handoff_id=data.get("handoff_id", handoff_id),
            status=data.get("status", "pending"),
            conversation_id=data.get("conversation_id", ""),
            priority=data.get("priority", "MEDIUM"),
            created_at=created_at,
            updated_at=updated_at,
            assigned_agent=data.get("assigned_agent"),
            ticket_id=data.get("ticket_id"),
            ticket_url=data.get("ticket_url"),
            resolution=data.get("resolution"),
            history=history
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving handoff {handoff_id}: {e}",
            extra={"handoff_id": handoff_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving handoff status: {str(e)}"
        )


@router.get(
    "/handoff",
    response_model=Dict[str, Any],
    summary="List Handoffs",
    description="List handoffs with pagination.",
    responses={
        500: {"model": ErrorResponse, "description": "Storage error"}
    }
)
async def list_handoffs(
    limit: int = 20,
    offset: int = 0,
    api_key: APIKey = Depends(get_api_key)
) -> Dict[str, Any]:
    """List all handoffs with pagination.

    Args:
        limit: Maximum number of results (default 20, max 100)
        offset: Offset for pagination

    Returns:
        Dictionary with handoffs list and pagination info
    """
    logger.info(
        f"Listing handoffs (limit={limit}, offset={offset})"
    )

    try:
        storage = get_handoff_storage()
        handoffs = await storage.list_all(limit=limit, offset=offset)
        total = await storage.count()

        # Convert datetime fields
        for h in handoffs:
            if "created_at" in h and isinstance(h["created_at"], str):
                h["created_at"] = h["created_at"]
            if "updated_at" in h and isinstance(h["updated_at"], str):
                h["updated_at"] = h["updated_at"]

        return {
            "handoffs": handoffs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + len(handoffs) < total,
            "has_previous": offset > 0
        }

    except Exception as e:
        logger.error(f"Error listing handoffs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing handoffs: {str(e)}"
        )


@router.get(
    "/conversation/{conversation_id}/handoffs",
    response_model=List[Dict[str, Any]],
    summary="List Handoffs by Conversation",
    description="List all handoffs for a specific conversation."
)
async def list_conversation_handoffs(
    conversation_id: str,
    limit: int = 10,
    api_key: APIKey = Depends(get_api_key)
) -> list[Dict[str, Any]]:
    """List all handoffs for a specific conversation.

    Args:
        conversation_id: Conversation identifier
        limit: Maximum number of results

    Returns:
        List of handoff data dictionaries
    """
    logger.info(
        f"Listing handoffs for conversation {conversation_id}"
    )

    try:
        storage = get_handoff_storage()
        handoffs = await storage.list_by_conversation(conversation_id, limit=limit)

        # Convert datetime fields
        for h in handoffs:
            if "created_at" in h and isinstance(h["created_at"], str):
                h["created_at"] = h["created_at"]
            if "updated_at" in h and isinstance(h["updated_at"], str):
                h["updated_at"] = h["updated_at"]

        return handoffs

    except Exception as e:
        logger.error(
            f"Error listing handoffs for conversation {conversation_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing handoffs: {str(e)}"
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
async def cancel_handoff(
    handoff_id: str,
    api_key: APIKey = Depends(get_api_key)
) -> dict:
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

    try:
        storage = get_handoff_storage()

        # Check if handoff exists
        handoff = await storage.get(handoff_id)
        if not handoff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Handoff with ID '{handoff_id}' not found"
            )

        # Update status to cancelled
        updated = await storage.update_status(
            handoff_id,
            "cancelled",
            {"resolution": "Cancelled by user"}
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to cancel handoff"
            )

        logger.info(f"Handoff {handoff_id} cancelled successfully")

        return {
            "message": f"Handoff {handoff_id} has been cancelled",
            "handoff_id": handoff_id,
            "status": "cancelled"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error cancelling handoff {handoff_id}: {e}",
            extra={"handoff_id": handoff_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling handoff: {str(e)}"
        )
