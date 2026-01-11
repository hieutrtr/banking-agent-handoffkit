"""Data models for fallback ticket creation."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from handoffkit.core.types import HandoffPriority


class FallbackStatus(str, Enum):
    """Status of a fallback ticket."""

    PENDING = "pending"
    RETRYING = "retrying"
    ASSIGNED = "assigned"
    EXPIRED = "expired"
    FAILED = "failed"


class FallbackReason(str, Enum):
    """Reason why fallback was used."""

    NO_AGENTS_AVAILABLE = "no_agents_available"
    AGENT_ASSIGNMENT_FAILED = "agent_assignment_failed"
    INTEGRATION_OFFLINE = "integration_offline"
    INTEGRATION_ERROR = "integration_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"


class FallbackTicket(BaseModel):
    """Represents a ticket created through fallback mechanism.

    Attributes:
        fallback_id: Local unique identifier for the fallback ticket
        handoff_id: Original handoff identifier
        integration_name: Name of the target integration
        ticket_data: Complete ticket data that would be sent to integration
        fallback_reason: Why fallback was used
        priority: Handoff priority level
        created_at: When the fallback ticket was created
        retry_count: Number of retry attempts made
        last_retry_at: Timestamp of last retry attempt
        status: Current status of the fallback ticket
        error_details: Optional error details for debugging
        estimated_wait_minutes: Estimated wait time for assignment
        queue_position: Position in queue (if available)
        retry_after: When to retry next (for rate limiting)
        original_context: Full conversation context
        metadata: Additional metadata
    """

    fallback_id: str = Field(description="Local unique identifier")
    handoff_id: str = Field(description="Original handoff identifier")
    integration_name: str = Field(description="Target integration name")
    ticket_data: dict[str, Any] = Field(description="Complete ticket data")
    fallback_reason: FallbackReason = Field(description="Why fallback was used")
    priority: HandoffPriority = Field(description="Handoff priority level")
    created_at: datetime = Field(description="Creation timestamp")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    last_retry_at: Optional[datetime] = Field(default=None, description="Last retry timestamp")
    status: FallbackStatus = Field(default=FallbackStatus.PENDING, description="Current status")
    error_details: Optional[str] = Field(default=None, description="Error details for debugging")
    estimated_wait_minutes: Optional[int] = Field(default=None, ge=0, description="Estimated wait time")
    queue_position: Optional[int] = Field(default=None, ge=0, description="Queue position")
    retry_after: Optional[datetime] = Field(default=None, description="When to retry next")
    original_context: dict[str, Any] = Field(description="Full conversation context")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def is_retryable(self) -> bool:
        """Check if this ticket should be retried."""
        if self.status in (FallbackStatus.ASSIGNED, FallbackStatus.EXPIRED, FallbackStatus.FAILED):
            return False

        # Don't retry if we've exceeded max attempts (12 = 1 hour at 5min intervals)
        if self.retry_count >= 12:
            return False

        # Don't retry if retry_after is set and not yet reached
        if self.retry_after and self.retry_after > datetime.now(timezone.utc):
            return False

        return True

    def should_retry_now(self) -> bool:
        """Check if this ticket should be retried now."""
        if not self.is_retryable():
            return False

        # If never retried, retry immediately
        if not self.last_retry_at:
            return True

        # Calculate next retry time with exponential backoff
        # Start at 5 minutes, double each time, max 60 minutes
        base_delay = 5  # minutes
        max_delay = 60  # minutes
        delay = min(base_delay * (2 ** self.retry_count), max_delay)

        next_retry = self.last_retry_at + timedelta(minutes=delay)
        return datetime.now(timezone.utc) >= next_retry

    def increment_retry(self) -> None:
        """Increment retry count and update timestamps."""
        self.retry_count += 1
        self.last_retry_at = datetime.now(timezone.utc)

    def mark_assigned(self, ticket_id: str, agent_id: Optional[str] = None) -> None:
        """Mark ticket as successfully assigned."""
        self.status = FallbackStatus.ASSIGNED
        self.metadata["assigned_ticket_id"] = ticket_id
        if agent_id:
            self.metadata["assigned_agent_id"] = agent_id

    def mark_failed(self, error: str) -> None:
        """Mark ticket as failed."""
        self.status = FallbackStatus.FAILED
        self.error_details = error

    def mark_expired(self) -> None:
        """Mark ticket as expired."""
        self.status = FallbackStatus.EXPIRED

    def get_retry_summary(self) -> dict[str, Any]:
        """Get summary of retry status."""
        return {
            "retry_count": self.retry_count,
            "max_retries": 12,
            "can_retry": self.is_retryable(),
            "should_retry_now": self.should_retry_now(),
            "last_retry": self.last_retry_at.isoformat() if self.last_retry_at else None,
            "next_retry": self._calculate_next_retry_time().isoformat() if self.is_retryable() else None,
        }

    def _calculate_next_retry_time(self) -> datetime:
        """Calculate when this ticket should be retried next."""
        if not self.last_retry_at:
            return self.created_at

        base_delay = 5  # minutes
        max_delay = 60  # minutes
        delay = min(base_delay * (2 ** self.retry_count), max_delay)

        return self.last_retry_at + timedelta(minutes=delay)

    def get_user_message(self) -> str:
        """Get appropriate user message based on fallback reason."""
        if self.fallback_reason == FallbackReason.NO_AGENTS_AVAILABLE:
            msg = "All agents are currently busy. Your request has been queued."
            if self.estimated_wait_minutes:
                msg += f" Estimated wait time: {self.estimated_wait_minutes} minutes."
            if self.queue_position:
                msg += f" Queue position: {self.queue_position}."
            return msg

        elif self.fallback_reason == FallbackReason.INTEGRATION_OFFLINE:
            return (
                "Our support system is temporarily offline. "
                f"Your ticket has been saved with reference: {self.fallback_id}. "
                "We will process it as soon as the system is back online."
            )

        elif self.fallback_reason == FallbackReason.AGENT_ASSIGNMENT_FAILED:
            return (
                "We couldn't assign your request to a specific agent immediately. "
                "Your ticket has been created and will be assigned shortly. "
                f"Ticket reference: {self.fallback_id}"
            )

        elif self.fallback_reason == FallbackReason.RATE_LIMIT_EXCEEDED:
            return (
                "We're experiencing high volume right now. "
                "Your request has been queued and will be processed shortly."
            )

        else:
            return (
                "Your request has been received and will be processed. "
                f"Reference: {self.fallback_id}"
            )


class FallbackMetrics(BaseModel):
    """Metrics for fallback ticket operations."""

    total_fallbacks: int = Field(default=0, ge=0)
    by_reason: dict[FallbackReason, int] = Field(default_factory=dict)
    by_status: dict[FallbackStatus, int] = Field(default_factory=dict)
    by_integration: dict[str, int] = Field(default_factory=dict)
    retry_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_retry_count: float = Field(default=0.0, ge=0.0)
    oldest_pending: Optional[datetime] = Field(default=None)
    queue_size: int = Field(default=0, ge=0)

    def record_fallback(self, ticket: FallbackTicket) -> None:
        """Record a new fallback ticket."""
        self.total_fallbacks += 1
        self.by_reason[ticket.fallback_reason] = self.by_reason.get(ticket.fallback_reason, 0) + 1
        self.by_status[ticket.status] = self.by_status.get(ticket.status, 0) + 1
        self.by_integration[ticket.integration_name] = self.by_integration.get(ticket.integration_name, 0) + 1

    def update_from_retry(self, ticket: FallbackTicket, success: bool) -> None:
        """Update metrics from retry attempt."""
        if success:
            # Calculate new success rate
            total_retries = sum(t.retry_count for t in self._get_all_tickets())
            successful_retries = sum(1 for t in self._get_all_tickets() if t.status == FallbackStatus.ASSIGNED)
            if total_retries > 0:
                self.retry_success_rate = successful_retries / total_retries

    def _get_all_tickets(self) -> list[FallbackTicket]:
        """Get all tickets (would be implemented by storage layer)."""
        # This would be connected to the storage system
        return []