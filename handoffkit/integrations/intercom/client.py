"""Intercom helpdesk integration.

Provides integration with Intercom for creating conversations,
checking agent availability, and managing handoff workflows.

Example:
    >>> from handoffkit.integrations.intercom import IntercomIntegration
    >>> integration = IntercomIntegration(
    ...     access_token="your-access-token",
    ...     app_id="your-app-id"
    ... )
    >>> await integration.initialize()
    >>> result = await integration.create_ticket(context, decision)
"""

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

logger = get_logger("integrations.intercom")

# Maximum note size for Intercom (10KB)
MAX_NOTE_SIZE = 10 * 1024


class IntercomIntegration(BaseIntegration):
    """Integration with Intercom platform.

    Supports:
    - Conversation handoff
    - Inbox assignment
    - Team member availability
    - Conversation tagging
    - Internal notes

    Requires Intercom API access token.

    Example:
        >>> integration = IntercomIntegration("access_token", "app_id")
        >>> await integration.initialize()
        >>> result = await integration.create_ticket(context, decision)
    """

    # Priority mapping from HandoffKit to Intercom
    # Note: Intercom uses simpler priority system (priority attribute for SLA)
    PRIORITY_MAP: dict[str, bool] = {
        "urgent": True,  # Mark as priority
        "high": True,    # Mark as priority
        "medium": False,  # Not prioritized
        "low": False,     # Not prioritized
    }

    @property
    def integration_name(self) -> str:
        return "intercom"

    @property
    def supported_features(self) -> list[str]:
        return [
            "conversation_handoff",
            "inbox_assignment",
            "team_availability",
            "tagging",
            "note_attachment",
        ]

    def __init__(
        self,
        access_token: str,
        app_id: Optional[str] = None,
    ) -> None:
        """Initialize Intercom integration.

        Args:
            access_token: Intercom API access token.
            app_id: Optional Intercom app ID (used for conversation URLs).
        """
        self._access_token = access_token
        self._app_id = app_id
        self._base_url = "https://api.intercom.io"
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        self._app_info: Optional[dict[str, Any]] = None
        self._admin_id: Optional[str] = None
        # Retry queue for failed handoffs (MVP: in-memory)
        self._retry_queue: deque[dict[str, Any]] = deque(maxlen=100)

    async def initialize(self) -> None:
        """Initialize HTTP client and validate credentials.

        Creates an authenticated httpx AsyncClient and validates
        the credentials by calling the Intercom /me endpoint.

        Raises:
            httpx.HTTPStatusError: If authentication fails.
        """
        logger.debug("Initializing Intercom integration")

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Intercom-Version": "2.11",
            },
            timeout=30.0,
        )

        # Validate credentials by calling /me
        response = await self._client.get("/me")
        response.raise_for_status()

        data = response.json()
        self._app_info = data.get("app", {})
        self._admin_id = data.get("id")

        # Extract app_id from response if not provided
        if not self._app_id and self._app_info:
            self._app_id = self._app_info.get("id_code")

        self._initialized = True

        app_name = self._app_info.get("name", "unknown") if self._app_info else "unknown"
        logger.info(f"Intercom authenticated for app: {app_name}")

    async def create_ticket(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> HandoffResult:
        """Create/update Intercom conversation for handoff.

        Args:
            context: Packaged conversation context including messages,
                metadata, and entities.
            decision: Handoff decision with priority and trigger info.

        Returns:
            HandoffResult with conversation details on success, or error info on failure.
        """
        if not self._initialized or self._client is None:
            logger.warning("Intercom integration not initialized, initializing now...")
            try:
                await self.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize Intercom: {e}")
                return HandoffResult(
                    success=False,
                    status=HandoffStatus.FAILED,
                    error_message=f"Intercom initialization failed: {e}",
                )

        try:
            # Find or create contact
            contact = await self._find_or_create_contact(context)

            # Format initial message for the conversation
            initial_message = self._format_initial_message(context, decision)

            # Create conversation
            payload = {
                "from": {
                    "type": "user",
                    "id": contact["id"],
                },
                "body": initial_message,
            }

            logger.debug("Creating Intercom conversation")

            response = await self._client.post("/conversations", json=payload)
            response.raise_for_status()

            data = response.json()
            # Handle both wrapped and unwrapped response formats
            conversation = data.get("conversation", data)
            conversation_id = conversation["id"]

            # Add detailed handoff note for agents (admin-only visibility)
            if self._admin_id:
                await self._add_handoff_note(conversation_id, context, decision)

            # Set priority on conversation based on mapping
            priority_value = decision.priority.value if decision.priority else "medium"
            is_priority = self.PRIORITY_MAP.get(priority_value, False)
            if is_priority:
                await self._set_conversation_priority(conversation_id, is_priority)

            # Build conversation URL
            conversation_url = self._build_conversation_url(conversation_id)

            logger.info(f"Created Intercom conversation: {conversation_id}")

            return HandoffResult(
                success=True,
                handoff_id=str(uuid.uuid4()),
                status=HandoffStatus.PENDING,
                ticket_id=conversation_id,
                ticket_url=conversation_url,
                metadata={"intercom_conversation": conversation},
            )

        except httpx.HTTPStatusError as e:
            error_msg = self._handle_http_error(e)
            logger.error(f"Intercom API error: {error_msg}")

            # Queue for retry if transient error
            if e.response.status_code in (429, 500, 502, 503, 504):
                self._queue_for_retry(context, decision, error_msg)

            return HandoffResult(
                success=False,
                status=HandoffStatus.FAILED,
                error_message=error_msg,
            )

        except httpx.ConnectError as e:
            error_msg = f"Network error connecting to Intercom: {e}"
            logger.error(error_msg)
            self._queue_for_retry(context, decision, error_msg)

            return HandoffResult(
                success=False,
                status=HandoffStatus.FAILED,
                error_message=error_msg,
            )

        except httpx.TimeoutException as e:
            error_msg = f"Request to Intercom timed out: {e}"
            logger.error(error_msg)
            self._queue_for_retry(context, decision, error_msg)

            return HandoffResult(
                success=False,
                status=HandoffStatus.FAILED,
                error_message=error_msg,
            )

        except Exception as e:
            error_msg = f"Unexpected error creating Intercom conversation: {e}"
            logger.error(error_msg)

            return HandoffResult(
                success=False,
                status=HandoffStatus.FAILED,
                error_message=error_msg,
            )

    async def _find_or_create_contact(
        self,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """Find existing contact or create new one.

        Args:
            context: Conversation context with user info.

        Returns:
            Contact dictionary with id and other details.

        Raises:
            httpx.HTTPStatusError: If API request fails.
        """
        if self._client is None:
            raise RuntimeError("Client not initialized")

        user_email = context.metadata.get("user_email")
        user_id = context.user_id or context.metadata.get("user_id")

        # Search by external_id first
        if user_id:
            search_payload = {
                "query": {
                    "field": "external_id",
                    "operator": "=",
                    "value": user_id,
                }
            }
            response = await self._client.post("/contacts/search", json=search_payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    logger.debug(f"Found contact by external_id: {user_id}")
                    return data["data"][0]

        # Search by email
        if user_email:
            search_payload = {
                "query": {
                    "field": "email",
                    "operator": "=",
                    "value": user_email,
                }
            }
            response = await self._client.post("/contacts/search", json=search_payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    logger.debug(f"Found contact by email: {user_email}")
                    return data["data"][0]

        # Create new contact
        external_id = user_id or f"handoff-{uuid.uuid4()}"
        create_payload: dict[str, Any] = {
            "role": "user",
            "external_id": external_id,
        }
        if user_email:
            create_payload["email"] = user_email

        logger.debug(f"Creating new contact with external_id: {external_id}")

        response = await self._client.post("/contacts", json=create_payload)
        response.raise_for_status()
        return response.json()

    def _format_initial_message(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> str:
        """Format the initial message for the conversation.

        Args:
            context: Conversation context.
            decision: Handoff decision.

        Returns:
            Formatted initial message.
        """
        # Determine trigger type
        trigger_type = "Manual handoff"
        if decision.trigger_results:
            first_trigger = decision.trigger_results[0]
            if first_trigger.trigger_type:
                trigger_type = first_trigger.trigger_type.value.replace("_", " ").title()

        # Get summary if available
        summary = context.metadata.get("conversation_summary", {})
        summary_text = ""
        if isinstance(summary, dict) and summary.get("summary_text"):
            summary_text = summary["summary_text"]
        elif isinstance(summary, str):
            summary_text = summary

        if summary_text:
            return f"[Handoff: {trigger_type}]\n\n{summary_text}"
        else:
            return f"[Handoff: {trigger_type}]\n\nA customer requires assistance. Please see the internal notes for full context."

    async def _set_conversation_priority(
        self,
        conversation_id: str,
        is_priority: bool,
    ) -> None:
        """Set priority attribute on an Intercom conversation.

        Args:
            conversation_id: Intercom conversation ID.
            is_priority: Whether to mark as priority (True) or not (False).
        """
        if self._client is None or not self._admin_id:
            logger.warning("Cannot set priority: client or admin_id not available")
            return

        payload = {
            "type": "admin",
            "admin_id": self._admin_id,
            "message_type": "assignment",
            "priority": "priority" if is_priority else "not_priority",
        }

        try:
            response = await self._client.post(
                f"/conversations/{conversation_id}/parts",
                json=payload,
            )
            response.raise_for_status()
            logger.debug(f"Set priority on conversation: {conversation_id}")
        except Exception as e:
            # Priority setting failure should not fail the handoff
            logger.warning(f"Failed to set conversation priority: {e}")

    async def _add_handoff_note(
        self,
        conversation_id: str,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Add detailed handoff note to conversation (admin-only visibility).

        Args:
            conversation_id: Intercom conversation ID.
            context: Conversation context.
            decision: Handoff decision.
        """
        if self._client is None or not self._admin_id:
            logger.warning("Cannot add note: client or admin_id not available")
            return

        note_body = self._format_conversation_note(context, decision)

        payload = {
            "message_type": "note",
            "type": "admin",
            "admin_id": self._admin_id,
            "body": note_body,
        }

        try:
            response = await self._client.post(
                f"/conversations/{conversation_id}/parts",
                json=payload,
            )
            response.raise_for_status()
            logger.debug(f"Added handoff note to conversation: {conversation_id}")
        except Exception as e:
            # Note addition failure should not fail the handoff
            logger.warning(f"Failed to add handoff note: {e}")

    def _format_conversation_note(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> str:
        """Format conversation context as Intercom admin note.

        Creates a markdown-formatted note with sections for:
        - Summary (if available)
        - Handoff reason/trigger
        - Conversation history
        - Extracted entities
        - Session metadata

        Args:
            context: Conversation context with messages and metadata.
            decision: Handoff decision with trigger info.

        Returns:
            Formatted note string, truncated to 10KB if needed.
        """
        sections = []

        # Summary section (from ConversationSummary if available)
        summary = context.metadata.get("conversation_summary", {})
        if isinstance(summary, dict) and summary.get("summary_text"):
            sections.append(f"<b>Summary</b>\n{summary['summary_text']}")
        elif isinstance(summary, str):
            sections.append(f"<b>Summary</b>\n{summary}")

        # Trigger reason
        if decision.trigger_results:
            trigger = decision.trigger_results[0]
            trigger_lines = ["<b>Handoff Reason</b>"]
            if trigger.trigger_type:
                trigger_lines.append(f"• Type: {trigger.trigger_type.value}")
            trigger_lines.append(f"• Confidence: {trigger.confidence:.0%}")
            if trigger.reason:
                trigger_lines.append(f"• Reason: {trigger.reason}")
            sections.append("\n".join(trigger_lines))

        # Conversation history (last 20 messages)
        if context.messages:
            history_lines = ["<b>Conversation History</b>"]
            for msg in context.messages[-20:]:
                speaker = "Customer" if msg.speaker.value == "user" else "AI Assistant"
                timestamp = ""
                if msg.timestamp:
                    timestamp = msg.timestamp.strftime("%H:%M:%S")
                content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                history_lines.append(f"<b>{speaker}</b> ({timestamp}): {content}")
            sections.append("\n".join(history_lines))

        # Extracted entities
        if context.entities:
            entity_lines = ["<b>Key Information</b>"]
            entities = context.entities
            if isinstance(entities, dict):
                for entity_type, value in list(entities.items())[:10]:
                    entity_lines.append(f"• {entity_type}: {value}")
            elif isinstance(entities, list):
                for entity in entities[:10]:
                    if hasattr(entity, "entity_type") and hasattr(entity, "value"):
                        entity_lines.append(f"• {entity.entity_type}: {entity.value}")
                    elif isinstance(entity, dict):
                        entity_lines.append(
                            f"• {entity.get('entity_type', 'Unknown')}: {entity.get('value', '')}"
                        )
            if len(entity_lines) > 1:
                sections.append("\n".join(entity_lines))

        # Session metadata
        meta_lines = ["<b>Session Info</b>"]
        added_keys: set[str] = set()

        # First add from context attributes (primary source)
        if context.user_id:
            meta_lines.append(f"• user_id: {context.user_id}")
            added_keys.add("user_id")
        if context.session_id:
            meta_lines.append(f"• session_id: {context.session_id}")
            added_keys.add("session_id")
        if context.channel:
            meta_lines.append(f"• channel: {context.channel}")
            added_keys.add("channel")

        # Then add from metadata (only if not already added)
        meta_keys = ["user_id", "session_id", "channel", "conversation_duration"]
        for key in meta_keys:
            if key in context.metadata and key not in added_keys:
                meta_lines.append(f"• {key}: {context.metadata[key]}")
                added_keys.add(key)

        if len(meta_lines) > 1:
            sections.append("\n".join(meta_lines))

        body = "\n\n".join(sections)

        # Truncate if exceeds max size (optimized - single encode)
        body_bytes = body.encode("utf-8")
        if len(body_bytes) > MAX_NOTE_SIZE:
            # Calculate how many bytes to keep (with margin for truncation message)
            truncation_msg = "\n\n... [Truncated due to size limits]"
            target_size = MAX_NOTE_SIZE - len(truncation_msg.encode("utf-8"))

            # Truncate bytes and decode safely
            truncated_bytes = body_bytes[:target_size]
            # Decode with errors='ignore' to handle partial UTF-8 sequences
            body = truncated_bytes.decode("utf-8", errors="ignore")
            body += truncation_msg

        return body

    def _build_conversation_url(self, conversation_id: str) -> str:
        """Build the Intercom inbox URL for a conversation.

        Args:
            conversation_id: Intercom conversation ID.

        Returns:
            URL to the conversation in Intercom inbox.
        """
        if self._app_id:
            return f"https://app.intercom.com/a/inbox/{self._app_id}/inbox/conversation/{conversation_id}"
        else:
            # Fallback URL without app_id
            return f"https://app.intercom.com/conversations/{conversation_id}"

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> str:
        """Handle HTTP errors and return user-friendly messages.

        Args:
            error: The HTTP status error from httpx.

        Returns:
            Human-readable error message.
        """
        status_code = error.response.status_code

        if status_code == 401:
            return "Intercom authentication failed: Invalid access token"
        elif status_code == 403:
            return "Intercom access denied: Insufficient permissions"
        elif status_code == 404:
            return "Intercom resource not found"
        elif status_code == 422:
            # Parse validation errors
            try:
                data = error.response.json()
                errors = data.get("errors", [])
                if errors:
                    details = "; ".join(e.get("message", str(e)) for e in errors)
                    return f"Intercom validation error: {details}"
                return f"Intercom validation error: {data}"
            except Exception:
                return f"Intercom validation error (422): {error.response.text[:200]}"
        elif status_code == 429:
            return "Intercom rate limit exceeded. Please retry later."
        elif status_code >= 500:
            return f"Intercom server error ({status_code}): Service temporarily unavailable"
        else:
            return f"Intercom API error ({status_code}): {error.response.text[:200]}"

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
        """Test the Intercom connection and credentials.

        Returns:
            Tuple of (success, message) indicating connection status.
        """
        try:
            if self._client is None:
                # Create temporary client for testing
                async with httpx.AsyncClient(
                    base_url=self._base_url,
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Intercom-Version": "2.11",
                    },
                    timeout=10.0,
                ) as client:
                    response = await client.get("/me")
                    response.raise_for_status()
                    data = response.json()
                    app_name = data.get("app", {}).get("name", "unknown")
                    return True, f"Connected successfully to app: {app_name}"
            else:
                response = await self._client.get("/me")
                response.raise_for_status()
                data = response.json()
                app_name = data.get("app", {}).get("name", "unknown")
                return True, f"Connected successfully to app: {app_name}"

        except httpx.HTTPStatusError as e:
            return False, self._handle_http_error(e)
        except httpx.ConnectError as e:
            return False, f"Connection failed: Unable to reach Intercom servers ({e})"
        except Exception as e:
            return False, f"Connection test failed: {e}"

    async def check_agent_availability(
        self,
        department: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Check Intercom team member availability.

        Note: Full implementation pending (Story 3.8).
        Currently returns empty list.

        Args:
            department: Optional department/team filter.

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
        """Assign conversation to Intercom team member.

        Note: Full implementation pending (Story 3.9).

        Args:
            ticket_id: ID of the conversation.
            agent_id: ID of the team member (admin).

        Returns:
            True if assignment succeeded.
        """
        # Placeholder for Story 3.9
        logger.debug(f"Agent assignment not yet implemented: conversation={ticket_id}")
        return False

    async def add_note(
        self,
        conversation_id: str,
        note: str,
    ) -> bool:
        """Add internal note to conversation.

        Args:
            conversation_id: Intercom conversation ID.
            note: Note content.

        Returns:
            True if note was added.
        """
        if not self._initialized or self._client is None:
            logger.warning("Intercom integration not initialized")
            return False

        if not self._admin_id:
            logger.warning("Admin ID not available for adding notes")
            return False

        try:
            payload = {
                "message_type": "note",
                "type": "admin",
                "admin_id": self._admin_id,
                "body": note,
            }

            response = await self._client.post(
                f"/conversations/{conversation_id}/parts",
                json=payload,
            )
            response.raise_for_status()
            logger.debug(f"Added note to conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add note: {e}")
            return False

    async def get_ticket_status(self, ticket_id: str) -> dict[str, Any]:
        """Get the current status of an Intercom conversation.

        Args:
            ticket_id: ID of the conversation.

        Returns:
            Conversation status information, or error info if request fails.
        """
        if not self._initialized or self._client is None:
            return {
                "ticket_id": ticket_id,
                "error": "Intercom integration not initialized",
            }

        try:
            response = await self._client.get(f"/conversations/{ticket_id}")
            response.raise_for_status()

            data = response.json()
            conversation = data.get("conversation", data)

            return {
                "ticket_id": ticket_id,
                "state": conversation.get("state"),
                "open": conversation.get("open"),
                "read": conversation.get("read"),
                "priority": conversation.get("priority"),
                "updated_at": conversation.get("updated_at"),
            }
        except httpx.HTTPStatusError as e:
            error_msg = self._handle_http_error(e)
            logger.error(f"Failed to get conversation status: {error_msg}")
            return {
                "ticket_id": ticket_id,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Unexpected error getting conversation status: {e}"
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
            logger.debug("Intercom integration closed")

    def get_retry_queue_size(self) -> int:
        """Get the number of items in the retry queue.

        Returns:
            Number of pending retry items.
        """
        return len(self._retry_queue)
