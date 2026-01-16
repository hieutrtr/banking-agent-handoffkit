"""Check endpoint for handoff decision evaluation."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status, Depends

from handoffkit.api.auth import get_api_key
from handoffkit.api.limiter import check_rate_limit
from handoffkit.api.models.auth import APIKey
from handoffkit.api.models.requests import CheckHandoffRequest, ConversationMessage
from handoffkit.api.models.responses import CheckResult, ErrorResponse
from handoffkit.core.types import ConversationContext, HandoffDecision, HandoffPriority, Message, Speaker
from handoffkit.core.exceptions import HandoffKitError

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
        speaker_enum = Speaker.USER  # Default to user if invalid

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


@router.post(
    "/check",
    response_model=CheckResult,
    summary="Check Handoff Recommendation",
    description="Evaluate a conversation and determine if handoff to a human is recommended.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal error"}
    }
)
async def check_handoff(
    request: CheckHandoffRequest,
    api_key: APIKey = Depends(get_api_key),
    rate_limit: bool = Depends(check_rate_limit)
) -> CheckResult:
    """Check if a conversation should be handed off to a human agent.

    This endpoint evaluates a conversation and returns a recommendation
    about whether handoff to a human agent is appropriate. It does not
    create any handoff records - it only provides recommendations.

    Args:
        request: CheckHandoffRequest containing conversation details

    Returns:
        CheckResult with handoff recommendation and confidence
    """
    logger.info(
        f"Checking handoff for conversation {request.conversation_id}",
        extra={
            "conversation_id": request.conversation_id,
            "user_id": request.user_id,
            "message_count": len(request.messages)
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

        # Create decision object (for evaluation only)
        decision = HandoffDecision(
            should_handoff=False,
            confidence=0.0,
            reason="",
            priority=HandoffPriority.MEDIUM,
            trigger_results=[]
        )

        # Call orchestrator to evaluate handoff
        from handoffkit import HandoffOrchestrator

        orchestrator = HandoffOrchestrator()

        # Evaluate handoff
        should_handoff = await orchestrator.should_handoff(context, decision)

        # Extract trigger information
        trigger_type = None
        trigger_confidence = None

        if decision.trigger_results:
            trigger_type = decision.trigger_results[0].trigger_type
            trigger_confidence = decision.trigger_results[0].confidence

        # Build metadata
        result_metadata: Dict[str, Any] = {}
        if decision.trigger_results:
            result_metadata = {
                "trigger_reason": decision.trigger_results[0].reason
            }

        logger.info(
            f"Handoff check result: should_handoff={should_handoff}, confidence={decision.confidence}",
            extra={
                "conversation_id": request.conversation_id,
                "should_handoff": should_handoff,
                "confidence": decision.confidence,
                "trigger_type": trigger_type
            }
        )

        return CheckResult(
            should_handoff=should_handoff,
            confidence=decision.confidence,
            reason=decision.reason,
            trigger_type=trigger_type,
            trigger_confidence=trigger_confidence,
            metadata=result_metadata
        )

    except ImportError as e:
        logger.error(f"Import error during handoff check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service configuration error: {str(e)}"
        )
    except HandoffKitError as e:
        logger.warning(f"Handoff evaluation error: {e}")
        # Return a safe result on handoff-specific errors
        return CheckResult(
            should_handoff=False,
            confidence=0.0,
            reason=f"Evaluation error: {str(e)}",
            metadata={"error_type": "handoff_error"}
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during handoff check: {e}",
            extra={
                "conversation_id": request.conversation_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during evaluation: {str(e)}"
        )


@router.post(
    "/check/batch",
    response_model=list[CheckResult],
    summary="Batch Check Handoff Recommendations",
    description="Check multiple conversations for handoff recommendations.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"}
    }
)
async def check_handoff_batch(
    requests: list[CheckHandoffRequest],
    api_key: APIKey = Depends(get_api_key),
    rate_limit: bool = Depends(check_rate_limit)
) -> list[CheckResult]:
    """Check multiple conversations for handoff recommendations.

    This endpoint evaluates multiple conversations in a single request,
    useful for batch processing or pre-screening.

    Args:
        requests: List of CheckHandoffRequest objects

    Returns:
        List of CheckResult objects, one per request
    """
    logger.info(
        f"Batch checking {len(requests)} conversations",
        extra={"batch_size": len(requests)}
    )

    results = []

    for request in requests:
        try:
            # Reuse single-request logic
            result = await check_handoff(request)
            results.append(result)
        except HTTPException as e:
            # For batch, return a failed result instead of raising
            results.append(CheckResult(
                should_handoff=False,
                confidence=0.0,
                reason=f"Request error: {e.detail}",
                metadata={"error": True}
            ))
        except Exception as e:
            results.append(CheckResult(
                should_handoff=False,
                confidence=0.0,
                reason=str(e),
                metadata={"error": True}
            ))

    logger.info(
        f"Batch check complete: {len(results)} results",
        extra={
            "total": len(results),
            "handoffs_recommended": sum(1 for r in results if r.should_handoff)
        }
    )

    return results