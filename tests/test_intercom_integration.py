"""Tests for Intercom integration.

Comprehensive tests covering:
- Initialization and authentication
- Conversation creation with full context
- Priority mapping
- Error handling (401, 403, 422, 429, network errors)
- Conversation note formatting
- Test connection functionality
- Retry queue
- Contact search/creation
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    HandoffStatus,
    Message,
    MessageSpeaker,
    TriggerResult,
    TriggerType,
)
from handoffkit.integrations.intercom import IntercomConfig, IntercomIntegration


class TestIntercomIntegrationInit:
    """Tests for IntercomIntegration initialization."""

    def test_init_stores_credentials(self) -> None:
        """Test that credentials are stored correctly."""
        integration = IntercomIntegration(
            access_token="test-token",
            app_id="app123",
        )

        assert integration._access_token == "test-token"
        assert integration._app_id == "app123"
        assert integration._base_url == "https://api.intercom.io"
        assert integration._initialized is False
        assert integration._client is None

    def test_init_app_id_optional(self) -> None:
        """Test that app_id is optional."""
        integration = IntercomIntegration(access_token="test-token")

        assert integration._app_id is None
        assert integration._access_token == "test-token"

    def test_integration_name(self) -> None:
        """Test integration_name property."""
        integration = IntercomIntegration("token")
        assert integration.integration_name == "intercom"

    def test_supported_features(self) -> None:
        """Test supported_features property."""
        integration = IntercomIntegration("token")
        features = integration.supported_features
        assert "conversation_handoff" in features
        assert "note_attachment" in features


class TestIntercomInitialize:
    """Tests for IntercomIntegration.initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_success(self) -> None:
        """Test successful initialization with valid credentials."""
        integration = IntercomIntegration("valid-token", "app123")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "admin123",
            "app": {"name": "Test App", "id_code": "app123"},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()

            assert integration._initialized is True
            assert integration._admin_id == "admin123"
            assert integration._app_info == {"name": "Test App", "id_code": "app123"}
            mock_client.get.assert_called_once_with("/me")

    @pytest.mark.asyncio
    async def test_initialize_creates_client_with_bearer_auth(self) -> None:
        """Test that initialize creates client with Bearer token auth."""
        integration = IntercomIntegration("my-access-token", "app123")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()

            # Verify AsyncClient was created with correct params
            call_kwargs = mock_client_class.call_args.kwargs
            assert call_kwargs["base_url"] == "https://api.intercom.io"
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == "Bearer my-access-token"
            assert call_kwargs["headers"]["Intercom-Version"] == "2.11"

    @pytest.mark.asyncio
    async def test_initialize_extracts_app_id_from_response(self) -> None:
        """Test that app_id is extracted from /me response if not provided."""
        integration = IntercomIntegration("token")  # No app_id provided

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "admin123",
            "app": {"name": "Test App", "id_code": "extracted-app-id"},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()

            assert integration._app_id == "extracted-app-id"

    @pytest.mark.asyncio
    async def test_initialize_auth_failure(self) -> None:
        """Test initialization fails with invalid credentials."""
        integration = IntercomIntegration("bad-token")

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Unauthorized", request=mock_request, response=mock_response
                )
            )
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await integration.initialize()

            assert integration._initialized is False


class TestCreateTicket:
    """Tests for IntercomIntegration.create_ticket()."""

    @pytest.fixture
    def context(self) -> ConversationContext:
        """Create a test conversation context."""
        return ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            session_id="sess-789",
            channel="chat",
            messages=[
                Message(speaker=MessageSpeaker.USER, content="I need help!"),
                Message(speaker=MessageSpeaker.AI, content="How can I assist?"),
            ],
            metadata={
                "user_email": "customer@example.com",
                "conversation_duration": "5 minutes",
            },
        )

    @pytest.fixture
    def decision(self) -> HandoffDecision:
        """Create a test handoff decision."""
        return HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.HIGH,
            trigger_results=[
                TriggerResult(
                    triggered=True,
                    trigger_type=TriggerType.DIRECT_REQUEST,
                    confidence=0.95,
                    reason="User explicitly requested human assistance",
                )
            ],
        )

    @pytest.mark.asyncio
    async def test_create_ticket_success(
        self, context: ConversationContext, decision: HandoffDecision
    ) -> None:
        """Test successful conversation creation."""
        integration = IntercomIntegration("token", "app123")

        # Mock initialization
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        # Mock contact search (found)
        contact_search_response = MagicMock()
        contact_search_response.status_code = 200
        contact_search_response.json.return_value = {
            "data": [{"id": "contact-123", "external_id": "user-456"}]
        }

        # Mock conversation creation
        conv_response = MagicMock()
        conv_response.status_code = 200
        conv_response.json.return_value = {"id": "conv-intercom-123"}
        conv_response.raise_for_status = MagicMock()

        # Mock note addition
        note_response = MagicMock()
        note_response.status_code = 200
        note_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(
                side_effect=[contact_search_response, conv_response, note_response]
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is True
            assert result.ticket_id == "conv-intercom-123"
            assert "app123" in result.ticket_url
            assert result.status == HandoffStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_ticket_creates_contact_when_not_found(
        self, decision: HandoffDecision
    ) -> None:
        """Test that a new contact is created when not found."""
        context = ConversationContext(
            conversation_id="conv-123",
            user_id="new-user-789",
            messages=[],
            metadata={"user_email": "newuser@example.com"},
        )

        integration = IntercomIntegration("token", "app123")

        # Mock initialization
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        # Mock contact search (not found)
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {"data": []}  # No contacts found

        # Mock contact creation
        create_contact_response = MagicMock()
        create_contact_response.status_code = 200
        create_contact_response.json.return_value = {"id": "new-contact-id"}
        create_contact_response.raise_for_status = MagicMock()

        # Mock conversation creation
        conv_response = MagicMock()
        conv_response.json.return_value = {"id": "conv-123"}
        conv_response.raise_for_status = MagicMock()

        # Mock note addition
        note_response = MagicMock()
        note_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            # Search by external_id, search by email, create contact, create conv, add note
            mock_client.post = AsyncMock(
                side_effect=[
                    search_response,  # search by external_id
                    search_response,  # search by email
                    create_contact_response,  # create contact
                    conv_response,  # create conversation
                    note_response,  # add note
                ]
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is True

            # Verify contact creation was called
            create_call = mock_client.post.call_args_list[2]
            assert create_call.args[0] == "/contacts"
            payload = create_call.kwargs["json"]
            assert payload["role"] == "user"
            assert payload["external_id"] == "new-user-789"
            assert payload["email"] == "newuser@example.com"


class TestPriorityMapping:
    """Tests for priority mapping."""

    def test_priority_map_structure(self) -> None:
        """Test priority mapping structure."""
        assert IntercomIntegration.PRIORITY_MAP["urgent"] is True
        assert IntercomIntegration.PRIORITY_MAP["high"] is True
        assert IntercomIntegration.PRIORITY_MAP["medium"] is False
        assert IntercomIntegration.PRIORITY_MAP["low"] is False

    @pytest.mark.asyncio
    async def test_priority_is_set_for_urgent_handoffs(self) -> None:
        """Test that priority is set on conversation for urgent/high priority handoffs."""
        integration = IntercomIntegration("token", "app123")

        context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            messages=[],
            metadata={"user_email": "test@test.com"},
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.URGENT,  # Should trigger priority setting
            trigger_results=[],
        )

        # Mock initialization
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        # Mock contact search (found)
        contact_search_response = MagicMock()
        contact_search_response.status_code = 200
        contact_search_response.json.return_value = {
            "data": [{"id": "contact-123", "external_id": "user-456"}]
        }

        # Mock conversation creation
        conv_response = MagicMock()
        conv_response.status_code = 200
        conv_response.json.return_value = {"id": "conv-intercom-123"}
        conv_response.raise_for_status = MagicMock()

        # Mock note addition and priority setting
        note_response = MagicMock()
        note_response.status_code = 200
        note_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            # contact search, create conv, add note, set priority
            mock_client.post = AsyncMock(
                side_effect=[
                    contact_search_response,
                    conv_response,
                    note_response,  # handoff note
                    note_response,  # priority setting
                ]
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is True

            # Verify priority setting was called (4th post call)
            assert mock_client.post.call_count == 4
            priority_call = mock_client.post.call_args_list[3]
            assert "/conversations/conv-intercom-123/parts" in priority_call.args[0]
            payload = priority_call.kwargs["json"]
            assert payload["priority"] == "priority"

    @pytest.mark.asyncio
    async def test_priority_not_set_for_medium_handoffs(self) -> None:
        """Test that priority is NOT set for medium/low priority handoffs."""
        integration = IntercomIntegration("token", "app123")

        context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            messages=[],
            metadata={"user_email": "test@test.com"},
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.MEDIUM,  # Should NOT trigger priority setting
            trigger_results=[],
        )

        # Mock initialization
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        # Mock contact search (found)
        contact_search_response = MagicMock()
        contact_search_response.status_code = 200
        contact_search_response.json.return_value = {
            "data": [{"id": "contact-123", "external_id": "user-456"}]
        }

        # Mock conversation creation
        conv_response = MagicMock()
        conv_response.status_code = 200
        conv_response.json.return_value = {"id": "conv-intercom-123"}
        conv_response.raise_for_status = MagicMock()

        # Mock note addition
        note_response = MagicMock()
        note_response.status_code = 200
        note_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            # contact search, create conv, add note (no priority setting)
            mock_client.post = AsyncMock(
                side_effect=[
                    contact_search_response,
                    conv_response,
                    note_response,  # handoff note only
                ]
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is True

            # Verify only 3 post calls (no priority setting)
            assert mock_client.post.call_count == 3


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def integration(self) -> IntercomIntegration:
        """Create an integration for testing."""
        return IntercomIntegration("token", "app123")

    @pytest.fixture
    def context(self) -> ConversationContext:
        """Create a test context."""
        return ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            messages=[],
            metadata={"user_email": "test@test.com"},
        )

    @pytest.fixture
    def decision(self) -> HandoffDecision:
        """Create a test decision."""
        return HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.MEDIUM,
            trigger_results=[],
        )

    @pytest.mark.asyncio
    async def test_error_401_authentication(
        self,
        integration: IntercomIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of 401 authentication error."""
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Unauthorized", request=mock_request, response=mock_response
                )
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is False
            assert result.status == HandoffStatus.FAILED
            assert "authentication failed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_error_403_forbidden(
        self,
        integration: IntercomIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of 403 forbidden error."""
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Forbidden", request=mock_request, response=mock_response
                )
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is False
            assert result.status == HandoffStatus.FAILED
            assert "access denied" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_error_422_validation(
        self,
        integration: IntercomIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of 422 validation error."""
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = '{"errors": [{"message": "Invalid contact"}]}'
        mock_response.json.return_value = {"errors": [{"message": "Invalid contact"}]}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Validation Error", request=mock_request, response=mock_response
                )
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is False
            assert result.status == HandoffStatus.FAILED
            assert "validation error" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_error_429_rate_limit(
        self,
        integration: IntercomIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of 429 rate limit error."""
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Rate Limit", request=mock_request, response=mock_response
                )
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is False
            assert result.status == HandoffStatus.FAILED
            assert "rate limit" in result.error_message.lower()
            # Should be queued for retry
            assert integration.get_retry_queue_size() == 1

    @pytest.mark.asyncio
    async def test_error_network_connection(
        self,
        integration: IntercomIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of network connection error."""
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is False
            assert result.status == HandoffStatus.FAILED
            assert "network error" in result.error_message.lower()
            # Should be queued for retry
            assert integration.get_retry_queue_size() == 1

    @pytest.mark.asyncio
    async def test_error_timeout(
        self,
        integration: IntercomIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of timeout error."""
        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is False
            assert result.status == HandoffStatus.FAILED
            assert "timed out" in result.error_message.lower()
            # Should be queued for retry
            assert integration.get_retry_queue_size() == 1


class TestConversationNoteFormatting:
    """Tests for conversation note formatting."""

    def test_format_note_includes_summary(self) -> None:
        """Test that summary is included in note."""
        integration = IntercomIntegration("token")

        context = ConversationContext(
            conversation_id="conv-123",
            messages=[],
            metadata={"conversation_summary": {"summary_text": "User has billing issue"}},
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.MEDIUM,
            trigger_results=[],
        )

        note = integration._format_conversation_note(context, decision)

        assert "<b>Summary</b>" in note
        assert "User has billing issue" in note

    def test_format_note_includes_trigger_reason(self) -> None:
        """Test that trigger reason is included."""
        integration = IntercomIntegration("token")

        context = ConversationContext(
            conversation_id="conv-123",
            messages=[],
            metadata={},
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.MEDIUM,
            trigger_results=[
                TriggerResult(
                    triggered=True,
                    trigger_type=TriggerType.SENTIMENT_ESCALATION,
                    confidence=0.85,
                    reason="User expressed frustration",
                )
            ],
        )

        note = integration._format_conversation_note(context, decision)

        assert "<b>Handoff Reason</b>" in note
        assert "sentiment_escalation" in note
        assert "85%" in note
        assert "User expressed frustration" in note

    def test_format_note_includes_conversation_history(self) -> None:
        """Test that conversation history is included."""
        integration = IntercomIntegration("token")

        context = ConversationContext(
            conversation_id="conv-123",
            messages=[
                Message(
                    speaker=MessageSpeaker.USER,
                    content="I need help with my account",
                    timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
                ),
                Message(
                    speaker=MessageSpeaker.AI,
                    content="How can I assist you?",
                    timestamp=datetime(2024, 1, 15, 10, 30, 5, tzinfo=timezone.utc),
                ),
            ],
            metadata={},
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.MEDIUM,
            trigger_results=[],
        )

        note = integration._format_conversation_note(context, decision)

        assert "<b>Conversation History</b>" in note
        assert "Customer" in note
        assert "AI Assistant" in note
        assert "I need help with my account" in note
        assert "How can I assist you?" in note

    def test_format_note_limits_messages(self) -> None:
        """Test that only last 20 messages are included."""
        integration = IntercomIntegration("token")

        # Create 30 messages
        messages = [
            Message(speaker=MessageSpeaker.USER, content=f"Message {i}")
            for i in range(30)
        ]

        context = ConversationContext(
            conversation_id="conv-123",
            messages=messages,
            metadata={},
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.MEDIUM,
            trigger_results=[],
        )

        note = integration._format_conversation_note(context, decision)

        # Should include messages 10-29 (last 20)
        assert "Message 10" in note
        assert "Message 29" in note
        # Should NOT include messages 0-9
        assert "Message 0\n" not in note
        assert "Message 9\n" not in note


class TestTestConnection:
    """Tests for test_connection method."""

    @pytest.mark.asyncio
    async def test_connection_success(self) -> None:
        """Test successful connection test."""
        integration = IntercomIntegration("token")

        mock_response = MagicMock()
        mock_response.json.return_value = {"app": {"name": "Test App"}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_context = AsyncMock()
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_context

            success, message = await integration.test_connection()

            assert success is True
            assert "Connected successfully" in message
            assert "Test App" in message

    @pytest.mark.asyncio
    async def test_connection_failure_auth(self) -> None:
        """Test connection failure with auth error."""
        integration = IntercomIntegration("bad-token")

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_context = AsyncMock()
            mock_context.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Unauthorized", request=mock_request, response=mock_response
                )
            )
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_context

            success, message = await integration.test_connection()

            assert success is False
            assert "authentication failed" in message.lower()


class TestIntercomConfig:
    """Tests for IntercomConfig model."""

    def test_config_valid(self) -> None:
        """Test valid config creation."""
        config = IntercomConfig(
            access_token="secret-token",
            app_id="app123",
        )

        assert config.access_token == "secret-token"
        assert config.app_id == "app123"

    def test_config_app_id_optional(self) -> None:
        """Test that app_id is optional."""
        config = IntercomConfig(access_token="token")

        assert config.access_token == "token"
        assert config.app_id is None

    def test_config_empty_token_fails(self) -> None:
        """Test that empty token fails validation."""
        with pytest.raises(ValueError, match="Access token cannot be empty"):
            IntercomConfig(access_token="")

    def test_config_whitespace_token_fails(self) -> None:
        """Test that whitespace-only token fails validation."""
        with pytest.raises(ValueError, match="Access token cannot be empty"):
            IntercomConfig(access_token="   ")

    def test_config_from_env(self) -> None:
        """Test loading config from environment."""
        with patch.dict(
            "os.environ",
            {
                "INTERCOM_ACCESS_TOKEN": "env-token",
                "INTERCOM_APP_ID": "env-app-id",
            },
        ):
            config = IntercomConfig.from_env()

            assert config is not None
            assert config.access_token == "env-token"
            assert config.app_id == "env-app-id"

    def test_config_from_env_token_only(self) -> None:
        """Test loading config with only token from environment."""
        with patch.dict(
            "os.environ",
            {"INTERCOM_ACCESS_TOKEN": "env-token"},
            clear=True,
        ):
            config = IntercomConfig.from_env()

            assert config is not None
            assert config.access_token == "env-token"
            assert config.app_id is None

    def test_config_from_env_missing(self) -> None:
        """Test that from_env returns None when token missing."""
        with patch.dict("os.environ", {}, clear=True):
            config = IntercomConfig.from_env()
            assert config is None

    def test_config_to_integration_kwargs(self) -> None:
        """Test conversion to integration kwargs."""
        config = IntercomConfig(
            access_token="secret",
            app_id="app123",
        )

        kwargs = config.to_integration_kwargs()

        assert kwargs["access_token"] == "secret"
        assert kwargs["app_id"] == "app123"

    def test_config_repr_hides_token(self) -> None:
        """Test that access_token is hidden in repr."""
        config = IntercomConfig(
            access_token="super-secret-token",
            app_id="app123",
        )

        repr_str = repr(config)
        assert "super-secret-token" not in repr_str


class TestRetryQueue:
    """Tests for retry queue functionality."""

    @pytest.mark.asyncio
    async def test_retry_queue_populated_on_transient_error(self) -> None:
        """Test that transient errors add to retry queue."""
        integration = IntercomIntegration("token")

        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            messages=[],
            metadata={"user_email": "test@test.com"},
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.MEDIUM,
            trigger_results=[],
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Service Unavailable", request=mock_request, response=mock_response
                )
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()

            assert integration.get_retry_queue_size() == 0
            await integration.create_ticket(context, decision)
            assert integration.get_retry_queue_size() == 1

    def test_retry_queue_max_size(self) -> None:
        """Test that retry queue has max size limit."""
        integration = IntercomIntegration("token")

        # Queue should have maxlen=100
        assert integration._retry_queue.maxlen == 100


class TestClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_cleans_up(self) -> None:
        """Test that close cleans up resources."""
        integration = IntercomIntegration("token")

        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            await integration.initialize()
            assert integration._initialized is True

            await integration.close()

            assert integration._initialized is False
            assert integration._client is None
            mock_client.aclose.assert_called_once()


class TestAddNote:
    """Tests for add_note method."""

    @pytest.mark.asyncio
    async def test_add_note_success(self) -> None:
        """Test successful note addition."""
        integration = IntercomIntegration("token")

        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        note_response = MagicMock()
        note_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(return_value=note_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.add_note("conv-123", "Test note content")

            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/conversations/conv-123/parts" in call_args.args[0]

    @pytest.mark.asyncio
    async def test_add_note_not_initialized(self) -> None:
        """Test add_note returns False when not initialized."""
        integration = IntercomIntegration("token")

        result = await integration.add_note("conv-123", "Note")

        assert result is False


class TestGetTicketStatus:
    """Tests for get_ticket_status method."""

    @pytest.mark.asyncio
    async def test_get_ticket_status_success(self) -> None:
        """Test successful conversation status retrieval."""
        integration = IntercomIntegration("token")

        init_response = MagicMock()
        init_response.json.return_value = {"id": "admin123", "app": {"name": "Test"}}
        init_response.raise_for_status = MagicMock()

        status_response = MagicMock()
        status_response.json.return_value = {
            "id": "conv-123",
            "state": "open",
            "open": True,
            "read": False,
            "priority": "priority",
            "updated_at": 1705320000,
        }
        status_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[init_response, status_response])
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.get_ticket_status("conv-123")

            assert result["ticket_id"] == "conv-123"
            assert result["state"] == "open"
            assert result["open"] is True
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_get_ticket_status_not_initialized(self) -> None:
        """Test get_ticket_status returns error when not initialized."""
        integration = IntercomIntegration("token")

        result = await integration.get_ticket_status("conv-123")

        assert result["ticket_id"] == "conv-123"
        assert "error" in result
        assert "not initialized" in result["error"]


class TestOrchestratorIntegration:
    """Tests for HandoffOrchestrator integration with Intercom."""

    @pytest.mark.asyncio
    async def test_orchestrator_uses_intercom_integration(self) -> None:
        """Test that HandoffOrchestrator uses IntercomIntegration when configured."""
        from handoffkit import HandoffOrchestrator, Message

        orchestrator = HandoffOrchestrator(helpdesk="intercom")

        # Create a mock integration
        mock_integration = AsyncMock()
        mock_integration.integration_name = "intercom"
        mock_integration.create_ticket = AsyncMock(
            return_value=MagicMock(
                success=True,
                handoff_id="test-123",
                ticket_id="conv-intercom-123",
                ticket_url="https://app.intercom.com/conversations/conv-intercom-123",
                status=HandoffStatus.PENDING,
                metadata={},
            )
        )

        # Use set_integration to inject mock
        orchestrator.set_integration(mock_integration)

        messages = [
            Message(speaker="user", content="I need help"),
        ]

        result = await orchestrator.create_handoff(messages, metadata={"user_id": "123"})

        # Verify the mock integration was called
        assert mock_integration.create_ticket.called
        assert result.success is True


class TestBuildConversationUrl:
    """Tests for _build_conversation_url method."""

    def test_url_with_app_id(self) -> None:
        """Test URL building with app_id."""
        integration = IntercomIntegration("token", "myapp123")
        url = integration._build_conversation_url("conv-abc")

        assert url == "https://app.intercom.com/a/inbox/myapp123/inbox/conversation/conv-abc"

    def test_url_without_app_id(self) -> None:
        """Test URL building without app_id."""
        integration = IntercomIntegration("token")
        url = integration._build_conversation_url("conv-abc")

        assert url == "https://app.intercom.com/conversations/conv-abc"
