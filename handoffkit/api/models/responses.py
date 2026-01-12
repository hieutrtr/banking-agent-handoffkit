"""Response models for HandoffKit REST API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Overall service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    components: Dict[str, Any] = Field(
        default_factory=dict,
        description="Status of individual components"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-01T12:00:00Z",
                "components": {
                    "database": "healthy",
                    "orchestrator": "healthy"
                }
            }
        }
    }


class CheckResult(BaseModel):
    """Response model for handoff check endpoint."""

    should_handoff: bool = Field(
        ...,
        description="Whether handoff is recommended"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the decision"
    )
    reason: str = Field(..., description="Reason for the decision")
    trigger_type: Optional[str] = Field(
        default=None,
        description="Type of trigger that was activated"
    )
    trigger_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence of the trigger"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional decision metadata"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "should_handoff": True,
                "confidence": 0.85,
                "reason": "Critical keyword detected",
                "trigger_type": "keyword_match",
                "trigger_confidence": 0.9,
                "metadata": {
                    "matched_keyword": "urgent"
                }
            }
        }
    }


class HandoffResponse(BaseModel):
    """Response model for handoff creation endpoint."""

    handoff_id: str = Field(..., description="Unique handoff identifier")
    status: str = Field(..., description="Handoff status")
    conversation_id: str = Field(..., description="Original conversation ID")
    user_id: str = Field(..., description="User ID")
    priority: str = Field(..., description="Handoff priority")
    ticket_id: Optional[str] = Field(
        default=None,
        description="Helpdesk ticket ID if created"
    )
    ticket_url: Optional[str] = Field(
        default=None,
        description="Helpdesk ticket URL if created"
    )
    assigned_agent: Optional[str] = Field(
        default=None,
        description="Assigned agent ID if applicable"
    )
    assigned_queue: Optional[str] = Field(
        default=None,
        description="Assigned queue if applicable"
    )
    routing_rule: Optional[str] = Field(
        default=None,
        description="Routing rule that was applied"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Handoff creation timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional handoff metadata"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "handoff_id": "ho-abc123",
                "status": "pending",
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "priority": "HIGH",
                "ticket_id": "TKT-12345",
                "ticket_url": "https://helpdesk.example.com/tickets/12345",
                "assigned_agent": None,
                "assigned_queue": "billing_support",
                "routing_rule": "billing_issues",
                "created_at": "2024-01-01T12:00:00Z",
                "metadata": {}
            }
        }
    }


class HandoffStatusResponse(BaseModel):
    """Response model for handoff status endpoint."""

    handoff_id: str = Field(..., description="Handoff identifier")
    status: str = Field(..., description="Current handoff status")
    conversation_id: str = Field(..., description="Original conversation ID")
    priority: str = Field(..., description="Handoff priority")
    created_at: datetime = Field(..., description="Handoff creation time")
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update time"
    )
    assigned_agent: Optional[str] = Field(
        default=None,
        description="Assigned agent ID"
    )
    ticket_id: Optional[str] = Field(
        default=None,
        description="Helpdesk ticket ID"
    )
    ticket_url: Optional[str] = Field(
        default=None,
        description="Helpdesk ticket URL"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Resolution status if completed"
    )
    history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Handoff status history"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "handoff_id": "ho-abc123",
                "status": "in_progress",
                "conversation_id": "conv-123",
                "priority": "HIGH",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:05:00Z",
                "assigned_agent": "agent-001",
                "ticket_id": "TKT-12345",
                "ticket_url": "https://helpdesk.example.com/tickets/12345",
                "resolution": None,
                "history": [
                    {"status": "pending", "timestamp": "2024-01-01T12:00:00Z"},
                    {"status": "in_progress", "timestamp": "2024-01-01T12:01:00Z"}
                ]
            }
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Any] = Field(
        default=None,
        description="Additional error details"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "validation_error",
                "message": "Invalid request data",
                "detail": {"field": "messages", "error": "Field required"},
                "request_id": "req-abc123",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    }


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel):
    """Base paginated response model."""

    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
