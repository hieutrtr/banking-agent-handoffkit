"""Zendesk helpdesk integration.

Provides integration with Zendesk Support for creating tickets,
checking agent availability, and managing handoff workflows.

Example:
    >>> from handoffkit.integrations.zendesk import ZendeskIntegration
    >>> integration = ZendeskIntegration(
    ...     subdomain="company",
    ...     email="admin@company.com",
    ...     api_token="your-api-token"
    ... )
    >>> await integration.initialize()
    >>> result = await integration.create_ticket(context, decision)
"""

import base64
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    HandoffResult,
    HandoffStatus,
)
from handoffkit.integrations.base import BaseIntegration
from handoffkit.utils.logging import get_logger

logger = get_logger("integrations.zendesk")

# Maximum description size for Zendesk tickets (64KB)
MAX_DESCRIPTION_SIZE = 64 * 1024


class ZendeskIntegration(BaseIntegration):
    """Integration with Zendesk helpdesk platform.

    Supports:
    - Ticket creation with context
    - Agent availability via Zendesk Talk/Chat
    - Ticket assignment
    - Status tracking

    Requires Zendesk API credentials:
    - subdomain: Your Zendesk subdomain (e.g., 'company' for company.zendesk.com)
    - email: Admin email for API access
    - api_token: Zendesk API token from Admin > Channels > API

    Example:
        >>> integration = ZendeskIntegration("company", "admin@co.com", "token")
        >>> await integration.initialize()
        >>> result = await integration.create_ticket(context, decision)
    """

    # Priority mapping from HandoffKit to Zendesk
    PRIORITY_MAP: dict[str, str] = {
        "immediate": "urgent",
        "urgent": "urgent",
        "high": "high",
        "medium": "normal",
        "normal": "normal",
        "low": "low",
    }

    @property
    def integration_name(self) -> str:
        return "zendesk"

    @property
    def supported_features(self) -> list[str]:
        return [
            "ticket_creation",
            "agent_availability",
            "ticket_assignment",
            "status_tracking",
            "priority_mapping",
        ]

    def __init__(
        self,
        subdomain: str,
        email: str,
        api_token: str,
    ) -> None:
        """Initialize Zendesk integration.

        Args:
            subdomain: Zendesk subdomain (e.g., 'company' for company.zendesk.com).
            email: Admin email for API access.
            api_token: Zendesk API token.
        """
        self._subdomain = subdomain
        self._email = email
        self._api_token = api_token
        self._base_url = f"https://{subdomain}.zendesk.com/api/v2"
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        self._authenticated_user: Optional[dict[str, Any]] = None
        # Retry queue for failed handoffs (MVP: in-memory)
        self._retry_queue: deque[dict[str, Any]] = deque(maxlen=100)

    async def initialize(self) -> None:
        """Initialize HTTP client and validate credentials.

        Creates an authenticated httpx AsyncClient and validates
        the credentials by calling the Zendesk users/me endpoint.

        Raises:
            httpx.HTTPStatusError: If authentication fails.
        """
        logger.debug(
            f"Initializing Zendesk integration for subdomain: {self._subdomain}"
        )

        # Zendesk API uses {email}/token:{api_token} for basic auth
        auth_string = f"{self._email}/token:{self._api_token}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Basic {auth_bytes}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        # Validate credentials by calling /users/me.json
        response = await self._client.get("/users/me.json")
        response.raise_for_status()

        data = response.json()
        self._authenticated_user = data.get("user", {})
        self._initialized = True

        logger.info(
            f"Zendesk authenticated as: {self._authenticated_user.get('email', 'unknown')}"
        )

    async def create_ticket(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> HandoffResult:
        """Create a Zendesk ticket with full conversation context.

        Args:
            context: Packaged conversation context including messages,
                metadata, and entities.
            decision: Handoff decision with priority and trigger info.

        Returns:
            HandoffResult with ticket details on success, or error info on failure.
        """
        if not self._initialized or self._client is None:
            logger.warning("Zendesk integration not initialized, initializing now...")
            try:
                await self.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize Zendesk: {e}")
                return HandoffResult(
                    success=False,
                    status=HandoffStatus.FAILED,
                    error_message=f"Zendesk initialization failed: {e}",
                )

        try:
            # Map priority
            priority_value = decision.priority.value if isinstance(
                decision.priority, HandoffPriority
            ) else str(decision.priority)
            zendesk_priority = self.PRIORITY_MAP.get(priority_value, "normal")

            # Format ticket body
            ticket_body = self._format_ticket_body(context, decision)

            # Determine subject from trigger
            trigger_type = "Manual"
            if decision.trigger_results:
                first_trigger = decision.trigger_results[0]
                if first_trigger.trigger_type:
                    trigger_type = first_trigger.trigger_type.value

            # Determine requester email
            user_email = context.metadata.get("user_email")
            if not user_email:
                user_id = context.user_id or context.metadata.get("user_id", "unknown")
                user_email = f"user-{user_id}@handoff.local"

            # Build ticket payload
            payload = {
                "ticket": {
                    "subject": f"Handoff: {trigger_type}",
                    "comment": {"body": ticket_body},
                    "priority": zendesk_priority,
                    "requester": {"email": user_email},
                    "tags": ["handoffkit", trigger_type.lower().replace("_", "-")],
                }
            }

            logger.debug(f"Creating Zendesk ticket with priority: {zendesk_priority}")

            response = await self._client.post("/tickets.json", json=payload)
            response.raise_for_status()

            data = response.json()
            ticket = data["ticket"]
            ticket_id = str(ticket["id"])
            ticket_url = f"https://{self._subdomain}.zendesk.com/agent/tickets/{ticket['id']}"

            logger.info(f"Created Zendesk ticket: {ticket_id}")

            return HandoffResult(
                success=True,
                handoff_id=str(uuid.uuid4()),
                status=HandoffStatus.PENDING,
                ticket_id=ticket_id,
                ticket_url=ticket_url,
                metadata={"zendesk_ticket": ticket},
            )

        except httpx.HTTPStatusError as e:
            error_msg = self._handle_http_error(e)
            logger.error(f"Zendesk API error: {error_msg}")

            # Queue for retry if transient error
            if e.response.status_code in (429, 500, 502, 503, 504):
                self._queue_for_retry(context, decision, error_msg)

            return HandoffResult(
                success=False,
                status=HandoffStatus.FAILED,
                error_message=error_msg,
            )

        except httpx.ConnectError as e:
            error_msg = f"Network error connecting to Zendesk: {e}"
            logger.error(error_msg)
            self._queue_for_retry(context, decision, error_msg)

            return HandoffResult(
                success=False,
                status=HandoffStatus.FAILED,
                error_message=error_msg,
            )

        except Exception as e:
            error_msg = f"Unexpected error creating Zendesk ticket: {e}"
            logger.error(error_msg)

            return HandoffResult(
                success=False,
                status=HandoffStatus.FAILED,
                error_message=error_msg,
            )

    def _format_ticket_body(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> str:
        """Format conversation context as Zendesk ticket body.

        Creates a markdown-formatted ticket description with sections for:
        - Summary (if available)
        - Handoff reason/trigger
        - Conversation history
        - Extracted entities
        - Session metadata

        Args:
            context: Conversation context with messages and metadata.
            decision: Handoff decision with trigger info.

        Returns:
            Formatted ticket body string, truncated to 64KB if needed.
        """
        sections = []

        # Summary section (from ConversationSummary if available)
        summary = context.metadata.get("conversation_summary", {})
        if isinstance(summary, dict) and summary.get("summary_text"):
            sections.append(f"## Summary\n{summary['summary_text']}")
        elif isinstance(summary, str):
            sections.append(f"## Summary\n{summary}")

        # Trigger reason
        if decision.trigger_results:
            trigger = decision.trigger_results[0]
            trigger_lines = ["## Handoff Reason"]
            if trigger.trigger_type:
                trigger_lines.append(f"- Type: {trigger.trigger_type.value}")
            trigger_lines.append(f"- Confidence: {trigger.confidence:.0%}")
            if trigger.reason:
                trigger_lines.append(f"- Reason: {trigger.reason}")
            sections.append("\n".join(trigger_lines))

        # Conversation history (last 20 messages)
        if context.messages:
            history_lines = ["## Conversation History"]
            for msg in context.messages[-20:]:
                speaker = "Customer" if msg.speaker.value == "user" else "AI Assistant"
                timestamp = ""
                if msg.timestamp:
                    timestamp = msg.timestamp.strftime("%H:%M:%S")
                content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                history_lines.append(f"**{speaker}** ({timestamp}): {content}")
            sections.append("\n".join(history_lines))

        # Extracted entities
        if context.entities:
            entity_lines = ["## Key Information"]
            entities = context.entities
            if isinstance(entities, dict):
                for entity_type, value in list(entities.items())[:10]:
                    entity_lines.append(f"- {entity_type}: {value}")
            elif isinstance(entities, list):
                for entity in entities[:10]:
                    if hasattr(entity, "entity_type") and hasattr(entity, "value"):
                        entity_lines.append(f"- {entity.entity_type}: {entity.value}")
                    elif isinstance(entity, dict):
                        entity_lines.append(
                            f"- {entity.get('entity_type', 'Unknown')}: {entity.get('value', '')}"
                        )
            if len(entity_lines) > 1:
                sections.append("\n".join(entity_lines))

        # Session metadata
        meta_lines = ["## Session Info"]
        # Track which keys we've already added to avoid duplicates
        added_keys = set()

        # First add from context attributes (primary source)
        if context.user_id:
            meta_lines.append(f"- user_id: {context.user_id}")
            added_keys.add("user_id")
        if context.session_id:
            meta_lines.append(f"- session_id: {context.session_id}")
            added_keys.add("session_id")
        if context.channel:
            meta_lines.append(f"- channel: {context.channel}")
            added_keys.add("channel")

        # Then add from metadata (only if not already added)
        meta_keys = ["user_id", "session_id", "channel", "conversation_duration"]
        for key in meta_keys:
            if key in context.metadata and key not in added_keys:
                meta_lines.append(f"- {key}: {context.metadata[key]}")
                added_keys.add(key)

        if len(meta_lines) > 1:
            sections.append("\n".join(meta_lines))

        body = "\n\n".join(sections)

        # Truncate if exceeds max size (optimized - single encode)
        body_bytes = body.encode("utf-8")
        if len(body_bytes) > MAX_DESCRIPTION_SIZE:
            # Calculate how many bytes to keep (with margin for truncation message)
            truncation_msg = "\n\n... [Truncated due to size limits]"
            target_size = MAX_DESCRIPTION_SIZE - len(truncation_msg.encode("utf-8"))

            # Truncate bytes and decode safely
            truncated_bytes = body_bytes[:target_size]
            # Decode with errors='ignore' to handle partial UTF-8 sequences
            body = truncated_bytes.decode("utf-8", errors="ignore")
            body += truncation_msg

        return body

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> str:
        """Handle HTTP errors and return user-friendly messages.

        Args:
            error: The HTTP status error from httpx.

        Returns:
            Human-readable error message.
        """
        status_code = error.response.status_code

        if status_code == 401:
            return "Zendesk authentication failed: Invalid API credentials"
        elif status_code == 403:
            return "Zendesk access denied: Insufficient permissions"
        elif status_code == 422:
            # Parse validation errors
            try:
                data = error.response.json()
                details = data.get("details", data.get("error", "Unknown validation error"))
                return f"Zendesk validation error: {details}"
            except Exception:
                return f"Zendesk validation error (422): {error.response.text[:200]}"
        elif status_code == 429:
            retry_after = error.response.headers.get("Retry-After", "unknown")
            return f"Zendesk rate limit exceeded. Retry after: {retry_after} seconds"
        elif status_code >= 500:
            return f"Zendesk server error ({status_code}): Service temporarily unavailable"
        else:
            return f"Zendesk API error ({status_code}): {error.response.text[:200]}"

    def _queue_for_retry(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
        error: str,
    ) -> None:
        """Queue a failed handoff for later retry.

        Args:
            context: The conversation context.
            decision: The handoff decision.
            error: The error message.
        """
        retry_item = {
            "context": context.model_dump(mode="json"),
            "decision": decision.model_dump(mode="json"),
            "error": error,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "retry_count": 0,
        }
        self._retry_queue.append(retry_item)
        logger.warning(
            f"Queued handoff for retry. Queue size: {len(self._retry_queue)}"
        )

    async def test_connection(self) -> tuple[bool, str]:
        """Test the Zendesk connection and credentials.

        Returns:
            Tuple of (success, message) indicating connection status.
        """
        try:
            if self._client is None:
                # Create temporary client for testing
                auth_string = f"{self._email}/token:{self._api_token}"
                auth_bytes = base64.b64encode(auth_string.encode()).decode()

                async with httpx.AsyncClient(
                    base_url=self._base_url,
                    headers={
                        "Authorization": f"Basic {auth_bytes}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                ) as client:
                    response = await client.get("/users/me.json")
                    response.raise_for_status()
                    data = response.json()
                    email = data.get("user", {}).get("email", "unknown")
                    return True, f"Connected successfully as {email}"
            else:
                response = await self._client.get("/users/me.json")
                response.raise_for_status()
                data = response.json()
                email = data.get("user", {}).get("email", "unknown")
                return True, f"Connected successfully as {email}"

        except httpx.HTTPStatusError as e:
            return False, self._handle_http_error(e)
        except httpx.ConnectError as e:
            return False, f"Connection failed: Unable to reach Zendesk servers ({e})"
        except Exception as e:
            return False, f"Connection test failed: {e}"

    async def check_agent_availability(
        self,
        department: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Check Zendesk agent availability.

        Note: Full implementation pending (Story 3.8).
        Currently returns empty list.

        Args:
            department: Optional department filter.

        Returns:
            List of available agent info.
        """
        # Placeholder for Story 3.8
        logger.debug("Agent availability check not yet implemented")
        return []

    async def assign_to_agent(
        self,
        ticket_id: str,
        agent_id: str,
    ) -> bool:
        """Assign ticket to Zendesk agent.

        Note: Full implementation pending (Story 3.9).

        Args:
            ticket_id: ID of the ticket.
            agent_id: ID of the agent.

        Returns:
            True if assignment succeeded.
        """
        # Placeholder for Story 3.9
        logger.debug(f"Agent assignment not yet implemented: ticket={ticket_id}")
        return False

    async def get_ticket_status(self, ticket_id: str) -> dict[str, Any]:
        """Get the current status of a Zendesk ticket.

        Args:
            ticket_id: ID of the ticket.

        Returns:
            Ticket status information, or error info if request fails.
        """
        if not self._initialized or self._client is None:
            return {
                "ticket_id": ticket_id,
                "error": "Zendesk integration not initialized",
            }

        try:
            response = await self._client.get(f"/tickets/{ticket_id}.json")
            response.raise_for_status()

            data = response.json()
            ticket = data.get("ticket", {})

            return {
                "ticket_id": ticket_id,
                "status": ticket.get("status"),
                "priority": ticket.get("priority"),
                "assignee_id": ticket.get("assignee_id"),
                "updated_at": ticket.get("updated_at"),
            }
        except httpx.HTTPStatusError as e:
            error_msg = self._handle_http_error(e)
            logger.error(f"Failed to get ticket status: {error_msg}")
            return {
                "ticket_id": ticket_id,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Unexpected error getting ticket status: {e}"
            logger.error(error_msg)
            return {
                "ticket_id": ticket_id,
                "error": error_msg,
            }

    async def close(self) -> None:
        """Clean up integration resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._initialized = False
            logger.debug("Zendesk integration closed")

    def get_retry_queue_size(self) -> int:
        """Get the number of items in the retry queue.

        Returns:
            Number of pending retry items.
        """
        return len(self._retry_queue)
