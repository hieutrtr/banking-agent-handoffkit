"""Tests for Zendesk integration.

Comprehensive tests covering:
- Initialization and authentication
- Ticket creation with full context
- Priority mapping
- Error handling (401, 403, 422, 429, network errors)
- Ticket body formatting
- Test connection functionality
- Retry queue
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
from handoffkit.integrations.zendesk import ZendeskConfig, ZendeskIntegration


class TestZendeskIntegrationInit:
    """Tests for ZendeskIntegration initialization."""

    def test_init_stores_credentials(self) -> None:
        """Test that credentials are stored correctly."""
        integration = ZendeskIntegration(
            subdomain="testcompany",
            email="admin@test.com",
            api_token="test-token",
        )

        assert integration._subdomain == "testcompany"
        assert integration._email == "admin@test.com"
        assert integration._api_token == "test-token"
        assert integration._base_url == "https://testcompany.zendesk.com/api/v2"
        assert integration._initialized is False
        assert integration._client is None

    def test_integration_name(self) -> None:
        """Test integration_name property."""
        integration = ZendeskIntegration("test", "test@test.com", "token")
        assert integration.integration_name == "zendesk"

    def test_supported_features(self) -> None:
        """Test supported_features property."""
        integration = ZendeskIntegration("test", "test@test.com", "token")
        features = integration.supported_features
        assert "ticket_creation" in features
        assert "priority_mapping" in features


class TestZendeskInitialize:
    """Tests for ZendeskIntegration.initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_success(self) -> None:
        """Test successful initialization with valid credentials."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user": {"email": "admin@test.com", "id": 123}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()

            assert integration._initialized is True
            assert integration._authenticated_user == {"email": "admin@test.com", "id": 123}
            mock_client.get.assert_called_once_with("/users/me.json")

    @pytest.mark.asyncio
    async def test_initialize_creates_client_with_auth(self) -> None:
        """Test that initialize creates client with correct auth header."""
        integration = ZendeskIntegration("myco", "admin@myco.com", "secret123")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user": {"email": "admin@myco.com"}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()

            # Verify AsyncClient was created with correct params
            call_kwargs = mock_client_class.call_args.kwargs
            assert call_kwargs["base_url"] == "https://myco.zendesk.com/api/v2"
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"].startswith("Basic ")

    @pytest.mark.asyncio
    async def test_initialize_auth_failure(self) -> None:
        """Test initialization fails with invalid credentials."""
        integration = ZendeskIntegration("test", "admin@test.com", "bad-token")

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
    """Tests for ZendeskIntegration.create_ticket()."""

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
        """Test successful ticket creation."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        # Mock initialization
        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        # Mock ticket creation
        ticket_response = MagicMock()
        ticket_response.status_code = 201
        ticket_response.json.return_value = {
            "ticket": {
                "id": 12345,
                "status": "new",
                "priority": "high",
            }
        }
        ticket_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(return_value=ticket_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.create_ticket(context, decision)

            assert result.success is True
            assert result.ticket_id == "12345"
            assert result.ticket_url == "https://test.zendesk.com/agent/tickets/12345"
            # Successful tickets start as PENDING until picked up by agent
            assert result.status == HandoffStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_ticket_uses_user_email_from_metadata(
        self, decision: HandoffDecision
    ) -> None:
        """Test that user email from metadata is used for requester."""
        context = ConversationContext(
            conversation_id="conv-123",
            messages=[],
            metadata={"user_email": "customer@example.com"},
        )

        integration = ZendeskIntegration("test", "admin@test.com", "token")

        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        ticket_response = MagicMock()
        ticket_response.json.return_value = {"ticket": {"id": 123}}
        ticket_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(return_value=ticket_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()
            await integration.create_ticket(context, decision)

            # Verify the requester email was set correctly
            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["ticket"]["requester"]["email"] == "customer@example.com"

    @pytest.mark.asyncio
    async def test_create_ticket_generates_placeholder_email(
        self, decision: HandoffDecision
    ) -> None:
        """Test that placeholder email is generated when no user_email."""
        context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            messages=[],
            metadata={},
        )

        integration = ZendeskIntegration("test", "admin@test.com", "token")

        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        ticket_response = MagicMock()
        ticket_response.json.return_value = {"ticket": {"id": 123}}
        ticket_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(return_value=ticket_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()
            await integration.create_ticket(context, decision)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["ticket"]["requester"]["email"] == "user-user-456@handoff.local"


class TestPriorityMapping:
    """Tests for priority mapping."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "handoffkit_priority,expected_zendesk",
        [
            (HandoffPriority.URGENT, "urgent"),
            (HandoffPriority.HIGH, "high"),
            (HandoffPriority.MEDIUM, "normal"),
            (HandoffPriority.LOW, "low"),
        ],
    )
    async def test_priority_mapping(
        self, handoffkit_priority: HandoffPriority, expected_zendesk: str
    ) -> None:
        """Test all priority mappings."""
        context = ConversationContext(
            conversation_id="conv-123",
            messages=[],
            metadata={"user_email": "test@test.com"},
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=handoffkit_priority,
            trigger_results=[],
        )

        integration = ZendeskIntegration("test", "admin@test.com", "token")

        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        ticket_response = MagicMock()
        ticket_response.json.return_value = {"ticket": {"id": 123}}
        ticket_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=init_response)
            mock_client.post = AsyncMock(return_value=ticket_response)
            mock_client_class.return_value = mock_client

            await integration.initialize()
            await integration.create_ticket(context, decision)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["ticket"]["priority"] == expected_zendesk


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def integration(self) -> ZendeskIntegration:
        """Create an initialized integration for testing."""
        return ZendeskIntegration("test", "admin@test.com", "token")

    @pytest.fixture
    def context(self) -> ConversationContext:
        """Create a test context."""
        return ConversationContext(
            conversation_id="conv-123",
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
        integration: ZendeskIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of 401 authentication error."""
        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
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
            assert "authentication failed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_error_403_forbidden(
        self,
        integration: ZendeskIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of 403 forbidden error."""
        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
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
            assert "access denied" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_error_422_validation(
        self,
        integration: ZendeskIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of 422 validation error."""
        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = '{"error": "Invalid requester"}'
        mock_response.json.return_value = {"error": "Invalid requester"}

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
            assert "validation error" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_error_429_rate_limit(
        self,
        integration: ZendeskIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of 429 rate limit error."""
        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_response.headers = {"Retry-After": "60"}

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
            assert "rate limit" in result.error_message.lower()
            # Should be queued for retry
            assert integration.get_retry_queue_size() == 1

    @pytest.mark.asyncio
    async def test_error_network_connection(
        self,
        integration: ZendeskIntegration,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> None:
        """Test handling of network connection error."""
        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
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
            assert "network error" in result.error_message.lower()
            # Should be queued for retry
            assert integration.get_retry_queue_size() == 1


class TestTicketBodyFormatting:
    """Tests for ticket body formatting."""

    def test_format_ticket_body_includes_summary(self) -> None:
        """Test that summary is included in ticket body."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        context = ConversationContext(
            conversation_id="conv-123",
            messages=[],
            metadata={
                "conversation_summary": {
                    "summary_text": "User has billing issue"
                }
            },
        )
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.MEDIUM,
            trigger_results=[],
        )

        body = integration._format_ticket_body(context, decision)

        assert "## Summary" in body
        assert "User has billing issue" in body

    def test_format_ticket_body_includes_trigger_reason(self) -> None:
        """Test that trigger reason is included."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

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

        body = integration._format_ticket_body(context, decision)

        assert "## Handoff Reason" in body
        assert "sentiment_escalation" in body
        assert "85%" in body
        assert "User expressed frustration" in body

    def test_format_ticket_body_includes_conversation_history(self) -> None:
        """Test that conversation history is included."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

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

        body = integration._format_ticket_body(context, decision)

        assert "## Conversation History" in body
        assert "Customer" in body
        assert "AI Assistant" in body
        assert "I need help with my account" in body
        assert "How can I assist you?" in body

    def test_format_ticket_body_limits_messages(self) -> None:
        """Test that only last 20 messages are included."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        # Create 30 messages
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=f"Message {i}",
            )
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

        body = integration._format_ticket_body(context, decision)

        # Should include messages 10-29 (last 20)
        assert "Message 10" in body
        assert "Message 29" in body
        # Should NOT include messages 0-9
        assert "Message 0\n" not in body
        assert "Message 9\n" not in body


class TestTestConnection:
    """Tests for test_connection method."""

    @pytest.mark.asyncio
    async def test_connection_success(self) -> None:
        """Test successful connection test."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        mock_response = MagicMock()
        mock_response.json.return_value = {"user": {"email": "admin@test.com"}}
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
            assert "admin@test.com" in message

    @pytest.mark.asyncio
    async def test_connection_failure_auth(self) -> None:
        """Test connection failure with auth error."""
        integration = ZendeskIntegration("test", "admin@test.com", "bad-token")

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


class TestZendeskConfig:
    """Tests for ZendeskConfig model."""

    def test_config_valid(self) -> None:
        """Test valid config creation."""
        config = ZendeskConfig(
            subdomain="mycompany",
            email="admin@mycompany.com",
            api_token="secret-token",
        )

        assert config.subdomain == "mycompany"
        assert config.email == "admin@mycompany.com"
        assert config.api_token == "secret-token"

    def test_config_strips_zendesk_url(self) -> None:
        """Test that full URL is stripped to subdomain."""
        config = ZendeskConfig(
            subdomain="https://mycompany.zendesk.com/",
            email="admin@mycompany.com",
            api_token="token",
        )

        assert config.subdomain == "mycompany"

    def test_config_email_validation(self) -> None:
        """Test email validation."""
        with pytest.raises(ValueError, match="Invalid email"):
            ZendeskConfig(
                subdomain="test",
                email="not-an-email",
                api_token="token",
            )

    def test_config_empty_token_fails(self) -> None:
        """Test that empty token fails validation."""
        with pytest.raises(ValueError, match="API token cannot be empty"):
            ZendeskConfig(
                subdomain="test",
                email="admin@test.com",
                api_token="",
            )

    def test_config_from_env(self) -> None:
        """Test loading config from environment."""
        with patch.dict(
            "os.environ",
            {
                "ZENDESK_SUBDOMAIN": "envcompany",
                "ZENDESK_EMAIL": "env@test.com",
                "ZENDESK_API_TOKEN": "env-token",
            },
        ):
            config = ZendeskConfig.from_env()

            assert config is not None
            assert config.subdomain == "envcompany"
            assert config.email == "env@test.com"
            assert config.api_token == "env-token"

    def test_config_from_env_missing(self) -> None:
        """Test that from_env returns None when vars missing."""
        with patch.dict("os.environ", {}, clear=True):
            config = ZendeskConfig.from_env()
            assert config is None

    def test_config_to_integration_kwargs(self) -> None:
        """Test conversion to integration kwargs."""
        config = ZendeskConfig(
            subdomain="mycompany",
            email="admin@mycompany.com",
            api_token="secret",
        )

        kwargs = config.to_integration_kwargs()

        assert kwargs["subdomain"] == "mycompany"
        assert kwargs["email"] == "admin@mycompany.com"
        assert kwargs["api_token"] == "secret"

    def test_config_repr_hides_token(self) -> None:
        """Test that api_token is hidden in repr."""
        config = ZendeskConfig(
            subdomain="mycompany",
            email="admin@mycompany.com",
            api_token="super-secret-token",
        )

        repr_str = repr(config)
        assert "super-secret-token" not in repr_str


class TestRetryQueue:
    """Tests for retry queue functionality."""

    @pytest.mark.asyncio
    async def test_retry_queue_populated_on_transient_error(self) -> None:
        """Test that transient errors add to retry queue."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        context = ConversationContext(
            conversation_id="conv-123",
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
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        # Queue should have maxlen=100
        assert integration._retry_queue.maxlen == 100


class TestClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_cleans_up(self) -> None:
        """Test that close cleans up resources."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
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


class TestOrchestratorIntegration:
    """Tests for HandoffOrchestrator integration with Zendesk."""

    @pytest.mark.asyncio
    async def test_orchestrator_uses_zendesk_integration(self) -> None:
        """Test that HandoffOrchestrator uses ZendeskIntegration when configured."""
        from handoffkit import HandoffOrchestrator, Message

        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Create a mock integration
        mock_integration = AsyncMock()
        mock_integration.integration_name = "zendesk"
        mock_integration.create_ticket = AsyncMock(
            return_value=MagicMock(
                success=True,
                handoff_id="test-123",
                ticket_id="12345",
                ticket_url="https://test.zendesk.com/agent/tickets/12345",
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

    @pytest.mark.asyncio
    async def test_set_integration_overrides_default(self) -> None:
        """Test that set_integration() allows custom integration injection."""
        from handoffkit import HandoffOrchestrator

        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Verify no integration initially
        assert orchestrator._integration is None

        # Create and set a custom mock integration
        mock_integration = AsyncMock()
        mock_integration.integration_name = "custom_zendesk"

        orchestrator.set_integration(mock_integration)

        # Verify integration was set
        assert orchestrator._integration == mock_integration


class TestGetTicketStatus:
    """Tests for get_ticket_status method."""

    @pytest.mark.asyncio
    async def test_get_ticket_status_success(self) -> None:
        """Test successful ticket status retrieval."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        status_response = MagicMock()
        status_response.json.return_value = {
            "ticket": {
                "id": 12345,
                "status": "open",
                "priority": "high",
                "assignee_id": 999,
                "updated_at": "2024-01-15T10:00:00Z",
            }
        }
        status_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[init_response, status_response])
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.get_ticket_status("12345")

            assert result["ticket_id"] == "12345"
            assert result["status"] == "open"
            assert result["priority"] == "high"
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_get_ticket_status_not_initialized(self) -> None:
        """Test get_ticket_status returns error when not initialized."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        result = await integration.get_ticket_status("12345")

        assert result["ticket_id"] == "12345"
        assert "error" in result
        assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_get_ticket_status_api_error(self) -> None:
        """Test get_ticket_status handles API errors gracefully."""
        integration = ZendeskIntegration("test", "admin@test.com", "token")

        init_response = MagicMock()
        init_response.json.return_value = {"user": {"email": "admin@test.com"}}
        init_response.raise_for_status = MagicMock()

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Ticket not found"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=[
                    init_response,
                    httpx.HTTPStatusError(
                        "Not Found", request=mock_request, response=mock_response
                    ),
                ]
            )
            mock_client_class.return_value = mock_client

            await integration.initialize()
            result = await integration.get_ticket_status("99999")

            assert result["ticket_id"] == "99999"
            assert "error" in result

