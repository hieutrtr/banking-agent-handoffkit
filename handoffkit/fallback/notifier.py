"""User notification system for fallback ticket scenarios."""

from datetime import datetime, timezone
from typing import Optional

from handoffkit.fallback.models import FallbackReason, FallbackTicket
from handoffkit.utils.logging import get_logger


class FallbackNotifier:
    """Handles user notifications for fallback ticket scenarios."""

    def __init__(self):
        """Initialize fallback notifier."""
        self._logger = get_logger("fallback.notifier")

    async def notify_user(
        self,
        ticket: FallbackTicket,
        queue_position: Optional[int] = None,
        estimated_wait_minutes: Optional[int] = None,
    ) -> str:
        """Generate and log appropriate user notification for fallback ticket.

        Args:
            ticket: The fallback ticket
            queue_position: Optional queue position
            estimated_wait_minutes: Optional estimated wait time

        Returns:
            The notification message sent to user
        """
        try:
            # Generate message based on fallback reason
            message = self._generate_message(
                ticket=ticket,
                queue_position=queue_position,
                estimated_wait_minutes=estimated_wait_minutes,
            )

            # Log the notification
            self._logger.info(
                "User notified of fallback ticket",
                extra={
                    "fallback_id": ticket.fallback_id,
                    "handoff_id": ticket.handoff_id,
                    "reason": ticket.fallback_reason.value,
                    "message": message,
                    "queue_position": queue_position,
                    "estimated_wait": estimated_wait_minutes,
                }
            )

            return message

        except Exception as e:
            self._logger.error(
                f"Failed to notify user: {e}",
                extra={"fallback_id": ticket.fallback_id, "error": str(e)},
            )
            # Return generic message on error
            return self._get_generic_message(ticket)

    async def notify_retry_attempt(
        self,
        ticket: FallbackTicket,
        attempt_number: int,
    ) -> None:
        """Notify user of retry attempt (for transparency).

        Args:
            ticket: The fallback ticket being retried
            attempt_number: Which retry attempt this is
        """
        try:
            if attempt_number <= 3:
                # Only notify for first few attempts to avoid spam
                message = (
                    f"We're still working on your request (attempt {attempt_number}). "
                    f"Reference: {ticket.fallback_id}"
                )

                self._logger.info(
                    "User notified of retry attempt",
                    extra={
                        "fallback_id": ticket.fallback_id,
                        "attempt_number": attempt_number,
                        "message": message,
                    }
                )

        except Exception as e:
            self._logger.error(
                f"Failed to notify retry attempt: {e}",
                extra={"fallback_id": ticket.fallback_id, "error": str(e)},
            )

    async def notify_assignment_success(
        self,
        ticket: FallbackTicket,
        ticket_id: str,
        agent_name: Optional[str] = None,
    ) -> str:
        """Notify user that fallback ticket was successfully assigned.

        Args:
            ticket: The original fallback ticket
            ticket_id: The assigned ticket ID
            agent_name: Optional agent name

        Returns:
            Success notification message
        """
        try:
            if agent_name:
                message = (
                    f"Great news! Your request has been assigned to {agent_name}. "
                    f"Ticket ID: {ticket_id}. Thank you for your patience."
                )
            else:
                message = (
                    f"Great news! Your request has been assigned to our team. "
                    f"Ticket ID: {ticket_id}. Thank you for your patience."
                )

            self._logger.info(
                "User notified of successful assignment",
                extra={
                    "fallback_id": ticket.fallback_id,
                    "ticket_id": ticket_id,
                    "agent_name": agent_name,
                    "message": message,
                }
            )

            return message

        except Exception as e:
            self._logger.error(
                f"Failed to notify assignment success: {e}",
                extra={"fallback_id": ticket.fallback_id, "error": str(e)},
            )
            return "Your request has been successfully assigned. Thank you for your patience."

    async def notify_assignment_failure(
        self,
        ticket: FallbackTicket,
        max_retries_reached: bool = False,
    ) -> str:
        """Notify user that fallback ticket could not be assigned.

        Args:
            ticket: The fallback ticket
            max_retries_reached: Whether max retries were exceeded

        Returns:
            Failure notification message
        """
        try:
            if max_retries_reached:
                message = (
                    "We apologize, but we were unable to assign your request after multiple attempts. "
                    "Your ticket remains in our system and will be manually reviewed. "
                    f"Reference: {ticket.fallback_id}"
                )
            else:
                message = (
                    "We're experiencing delays in assigning your request. "
                    "It remains in our queue and will be processed as soon as possible. "
                    f"Reference: {ticket.fallback_id}"
                )

            self._logger.warning(
                "User notified of assignment failure",
                extra={
                    "fallback_id": ticket.fallback_id,
                    "max_retries_reached": max_retries_reached,
                    "retry_count": ticket.retry_count,
                    "message": message,
                }
            )

            return message

        except Exception as e:
            self._logger.error(
                f"Failed to notify assignment failure: {e}",
                extra={"fallback_id": ticket.fallback_id, "error": str(e)},
            )
            return (
                "We're working on your request. "
                f"Reference: {ticket.fallback_id}"
            )

    def _generate_message(
        self,
        ticket: FallbackTicket,
        queue_position: Optional[int] = None,
        estimated_wait_minutes: Optional[int] = None,
    ) -> str:
        """Generate appropriate message based on fallback reason.

        Args:
            ticket: The fallback ticket
            queue_position: Optional queue position
            estimated_wait_minutes: Optional estimated wait time

        Returns:
            Generated message
        """
        if ticket.fallback_reason == FallbackReason.NO_AGENTS_AVAILABLE:
            return self._format_no_agents_message(ticket, queue_position, estimated_wait_minutes)

        elif ticket.fallback_reason == FallbackReason.INTEGRATION_OFFLINE:
            return self._format_offline_message(ticket)

        elif ticket.fallback_reason == FallbackReason.AGENT_ASSIGNMENT_FAILED:
            return self._format_assignment_failed_message(ticket)

        elif ticket.fallback_reason == FallbackReason.RATE_LIMIT_EXCEEDED:
            return self._format_rate_limit_message(ticket)

        elif ticket.fallback_reason == FallbackReason.TIMEOUT:
            return self._format_timeout_message(ticket)

        else:
            return self._format_generic_message(ticket)

    def _format_no_agents_message(
        self,
        ticket: FallbackTicket,
        queue_position: Optional[int],
        estimated_wait_minutes: Optional[int],
    ) -> str:
        """Format message for no agents available scenario."""
        parts = ["All agents are currently busy. Your request has been queued."]

        if queue_position:
            parts.append(f"Queue position: {queue_position}.")

        if estimated_wait_minutes:
            parts.append(f"Estimated wait time: {estimated_wait_minutes} minutes.")

        parts.append(f"Reference: {ticket.fallback_id}")

        return " ".join(parts)

    def _format_offline_message(self, ticket: FallbackTicket) -> str:
        """Format message for integration offline scenario."""
        return (
            "Our support system is temporarily offline. "
            f"Your ticket has been saved with reference: {ticket.fallback_id}. "
            "We will process it as soon as the system is back online. "
            "You can continue with your conversation, and we'll sync everything once we're back."
        )

    def _format_assignment_failed_message(self, ticket: FallbackTicket) -> str:
        """Format message for assignment failure scenario."""
        return (
            "We couldn't assign your request to a specific agent immediately. "
            "Your ticket has been created and will be assigned shortly. "
            f"Reference: {ticket.fallback_id}"
        )

    def _format_rate_limit_message(self, ticket: FallbackTicket) -> str:
        """Format message for rate limit scenario."""
        return (
            "We're experiencing high volume right now. "
            "Your request has been queued and will be processed shortly. "
            f"Reference: {ticket.fallback_id}"
        )

    def _format_timeout_message(self, ticket: FallbackTicket) -> str:
        """Format message for timeout scenario."""
        return (
            "We're taking longer than expected to process your request. "
            "Your ticket has been saved and will be processed. "
            f"Reference: {ticket.fallback_id}"
        )

    def _format_generic_message(self, ticket: FallbackTicket) -> str:
        """Format generic fallback message."""
        return (
            "Your request has been received and will be processed. "
            f"Reference: {ticket.fallback_id}"
        )

    def _get_generic_message(self, ticket: FallbackTicket) -> str:
        """Get generic message when specific formatting fails."""
        return f"Your request is being processed. Reference: {ticket.fallback_id}"