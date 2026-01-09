"""Tests for Generic JSON and Markdown Adapters (Story 3.7)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from handoffkit.context.adapters.json_adapter import JSONAdapter
from handoffkit.context.adapters.markdown_adapter import MarkdownAdapter
from handoffkit.core.orchestrator import HandoffOrchestrator
from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    HandoffResult,
    HandoffStatus,
    Message,
    MessageSpeaker,
    TriggerType,
)
from handoffkit.integrations.generic import GenericIntegration
from handoffkit.integrations.markdown import MarkdownIntegration


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_messages() -> list[Message]:
    """Create sample messages for testing."""
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    return [
        Message(
            speaker=MessageSpeaker.USER,
            content="Hello, I need help with my account",
            timestamp=base_time,
        ),
        Message(
            speaker=MessageSpeaker.AI,
            content="I'd be happy to help you with your account. What seems to be the issue?",
            timestamp=datetime(2024, 1, 15, 10, 0, 30, tzinfo=timezone.utc),
        ),
        Message(
            speaker=MessageSpeaker.USER,
            content="I can't access my account number 12345678",
            timestamp=datetime(2024, 1, 15, 10, 1, 0, tzinfo=timezone.utc),
        ),
    ]


@pytest.fixture
def sample_context(sample_messages: list[Message]) -> ConversationContext:
    """Create sample conversation context for testing."""
    return ConversationContext(
        conversation_id="conv-test-123",
        user_id="user-456",
        session_id="session-789",
        channel="web",
        messages=sample_messages,
        entities={
            "account_number": [{"masked_value": "****5678", "original_value": "12345678"}],
            "email": "test@example.com",
        },
        metadata={
            "conversation_summary": {
                "summary_text": "User needs help accessing their account.",
                "issue": "Account access issue",
            },
            "conversation_duration": 60,
        },
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_decision() -> HandoffDecision:
    """Create sample handoff decision for testing."""
    return HandoffDecision(
        should_handoff=True,
        priority=HandoffPriority.MEDIUM,
        trigger_results=[],
    )


# ============================================================================
# MarkdownAdapter Tests
# ============================================================================


class TestMarkdownAdapter:
    """Tests for MarkdownAdapter.convert()."""

    def test_adapter_properties(self) -> None:
        """Test adapter name and output format properties."""
        adapter = MarkdownAdapter()
        assert adapter.adapter_name == "markdown"
        assert adapter.output_format == "markdown"

    def test_convert_basic(self, sample_context: ConversationContext) -> None:
        """Test basic conversion to markdown."""
        adapter = MarkdownAdapter()
        result = adapter.convert(sample_context)

        # Check header
        assert "# Handoff Context: conv-test-123" in result
        assert "**Created:**" in result

        # Check session info
        assert "## Session Info" in result
        assert "**User ID:** user-456" in result
        assert "**Session ID:** session-789" in result
        assert "**Channel:** web" in result

    def test_convert_with_summary(self, sample_context: ConversationContext) -> None:
        """Test conversion includes summary when enabled."""
        adapter = MarkdownAdapter(include_summary=True)
        result = adapter.convert(sample_context)

        assert "## Summary" in result
        assert "User needs help accessing their account." in result

    def test_convert_without_summary(self, sample_context: ConversationContext) -> None:
        """Test conversion excludes summary when disabled."""
        adapter = MarkdownAdapter(include_summary=False)
        result = adapter.convert(sample_context)

        # Summary section should not appear
        assert "## Summary" not in result

    def test_convert_with_entities(self, sample_context: ConversationContext) -> None:
        """Test conversion includes entities when enabled."""
        adapter = MarkdownAdapter(include_entities=True)
        result = adapter.convert(sample_context)

        assert "## Key Information" in result
        assert "Account Number" in result
        assert "****5678" in result

    def test_convert_without_entities(self, sample_context: ConversationContext) -> None:
        """Test conversion excludes entities when disabled."""
        adapter = MarkdownAdapter(include_entities=False)
        result = adapter.convert(sample_context)

        assert "## Key Information" not in result

    def test_convert_conversation_history(
        self, sample_context: ConversationContext
    ) -> None:
        """Test conversation history section."""
        adapter = MarkdownAdapter()
        result = adapter.convert(sample_context)

        assert "## Conversation History" in result
        assert "**User**" in result
        assert "**AI**" in result
        assert "Hello, I need help with my account" in result

    def test_convert_truncates_history(self) -> None:
        """Test that history is truncated to last 10 messages when include_full_history=False."""
        # Create 15 messages
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=f"Message {i}",
                timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            )
            for i in range(15)
        ]
        context = ConversationContext(
            conversation_id="conv-123",
            messages=messages,
        )

        adapter = MarkdownAdapter(include_full_history=False, max_messages=10)
        result = adapter.convert(context)

        # Should mention truncation
        assert "Showing last 10 of 15 messages" in result
        # First messages should not be present
        assert "Message 0" not in result
        assert "Message 4" not in result
        # Last messages should be present
        assert "Message 14" in result

    def test_convert_truncates_custom_limit(self) -> None:
        """Test that history can be truncated to a custom number of messages."""
        # Create 10 messages
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=f"Message {i}",
                timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            )
            for i in range(10)
        ]
        context = ConversationContext(
            conversation_id="conv-123",
            messages=messages,
        )

        adapter = MarkdownAdapter(include_full_history=False, max_messages=3)
        result = adapter.convert(context)

        # Should mention truncation with custom limit
        assert "Showing last 3 of 10 messages" in result
        # First messages should not be present
        assert "Message 0" not in result
        assert "Message 6" not in result
        # Last messages should be present
        assert "Message 9" in result

    def test_convert_full_history(self) -> None:
        """Test that full history is included when include_full_history=True."""
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=f"Message {i}",
                timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            )
            for i in range(15)
        ]
        context = ConversationContext(
            conversation_id="conv-123",
            messages=messages,
        )

        adapter = MarkdownAdapter(include_full_history=True)
        result = adapter.convert(context)

        # All messages should be present
        assert "Message 0" in result
        assert "Message 14" in result
        assert "Showing last 10" not in result

    def test_convert_empty_messages(self) -> None:
        """Test conversion with no messages."""
        context = ConversationContext(
            conversation_id="conv-123",
            messages=[],
        )

        adapter = MarkdownAdapter()
        result = adapter.convert(context)

        assert "*No messages in conversation*" in result

    def test_convert_duration_in_metadata(
        self, sample_context: ConversationContext
    ) -> None:
        """Test that duration is included from metadata."""
        adapter = MarkdownAdapter()
        result = adapter.convert(sample_context)

        assert "**Duration:** 60 seconds" in result

    def test_entity_type_formatting(self) -> None:
        """Test that entity types are formatted properly (snake_case to Title Case)."""
        adapter = MarkdownAdapter()
        assert adapter._format_entity_type("account_number") == "Account Number"
        assert adapter._format_entity_type("phone") == "Phone"
        assert adapter._format_entity_type("user_email_address") == "User Email Address"


# ============================================================================
# JSONAdapter Tests
# ============================================================================


class TestJSONAdapter:
    """Tests for JSONAdapter enhancements."""

    def test_adapter_properties(self) -> None:
        """Test adapter name and output format properties."""
        adapter = JSONAdapter()
        assert adapter.adapter_name == "json"
        assert adapter.output_format == "json"

    def test_convert_basic(self, sample_context: ConversationContext) -> None:
        """Test basic JSON conversion."""
        adapter = JSONAdapter(pretty=True)
        result = adapter.convert(sample_context)

        # Should be valid JSON
        import json

        data = json.loads(result)
        assert data["conversation_id"] == "conv-test-123"
        assert data["user_id"] == "user-456"

    def test_convert_without_metadata(self, sample_context: ConversationContext) -> None:
        """Test conversion excludes metadata when disabled."""
        adapter = JSONAdapter(include_metadata=False)
        result = adapter.convert(sample_context)

        import json

        data = json.loads(result)
        assert "metadata" not in data

    def test_convert_to_dict(self, sample_context: ConversationContext) -> None:
        """Test convert_to_dict returns dictionary."""
        adapter = JSONAdapter()
        result = adapter.convert_to_dict(sample_context)

        assert isinstance(result, dict)
        assert result["conversation_id"] == "conv-test-123"

    def test_convert_to_handoff_package(
        self, sample_context: ConversationContext
    ) -> None:
        """Test convert_to_handoff_package returns structured package."""
        adapter = JSONAdapter()
        result = adapter.convert_to_handoff_package(
            sample_context,
            trigger_type="direct_request",
            priority="medium",
        )

        assert "conversation" in result
        assert "summary" in result
        assert "entities" in result
        assert "metadata" in result
        assert "handoff_info" in result

        assert result["conversation"]["id"] == "conv-test-123"
        assert result["handoff_info"]["trigger_type"] == "direct_request"
        assert result["handoff_info"]["priority"] == "medium"

    def test_exclude_empty_fields(self) -> None:
        """Test exclude_empty_fields removes empty values."""
        context = ConversationContext(
            conversation_id="conv-123",
            messages=[],
            entities={},
            metadata={},
        )

        adapter = JSONAdapter(exclude_empty_fields=True)
        result = adapter.convert_to_dict(context)

        # Empty fields should be removed
        assert "entities" not in result or result.get("entities") != {}
        assert "messages" not in result or result.get("messages") != []


# ============================================================================
# GenericIntegration Tests
# ============================================================================


class TestGenericIntegration:
    """Tests for GenericIntegration."""

    def test_integration_properties(self) -> None:
        """Test integration name and supported features."""
        integration = GenericIntegration()
        assert integration.integration_name == "json"
        assert "create_ticket" in integration.supported_features
        assert "export_json" in integration.supported_features

    @pytest.mark.asyncio
    async def test_initialize(self) -> None:
        """Test initialization (should be no-op)."""
        integration = GenericIntegration()
        await integration.initialize()
        assert integration._initialized is True

    @pytest.mark.asyncio
    async def test_create_ticket_success(
        self,
        sample_context: ConversationContext,
        sample_decision: HandoffDecision,
    ) -> None:
        """Test create_ticket returns valid HandoffResult."""
        integration = GenericIntegration()
        await integration.initialize()

        result = await integration.create_ticket(sample_context, sample_decision)

        assert result.success is True
        assert result.status == HandoffStatus.PENDING
        assert result.handoff_id is not None
        assert result.ticket_id == result.handoff_id
        assert result.ticket_url is None  # No external URL
        assert "json_content" in result.metadata
        assert "handoff_package" in result.metadata
        assert result.metadata["export_format"] == "json"

    @pytest.mark.asyncio
    async def test_create_ticket_auto_initializes(
        self,
        sample_context: ConversationContext,
        sample_decision: HandoffDecision,
    ) -> None:
        """Test create_ticket auto-initializes if not initialized."""
        integration = GenericIntegration()
        # Don't call initialize()

        result = await integration.create_ticket(sample_context, sample_decision)

        assert result.success is True
        assert integration._initialized is True

    @pytest.mark.asyncio
    async def test_check_agent_availability(self) -> None:
        """Test check_agent_availability returns empty list."""
        integration = GenericIntegration()
        result = await integration.check_agent_availability()
        assert result == []

    @pytest.mark.asyncio
    async def test_assign_to_agent(self) -> None:
        """Test assign_to_agent returns False."""
        integration = GenericIntegration()
        result = await integration.assign_to_agent("ticket-123", "agent-456")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_ticket_status(self) -> None:
        """Test get_ticket_status returns local status."""
        integration = GenericIntegration()
        result = await integration.get_ticket_status("ticket-123")
        assert result["ticket_id"] == "ticket-123"
        assert result["status"] == "local"

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test close resets initialized state."""
        integration = GenericIntegration()
        await integration.initialize()
        assert integration._initialized is True

        await integration.close()
        assert integration._initialized is False


# ============================================================================
# MarkdownIntegration Tests
# ============================================================================


class TestMarkdownIntegration:
    """Tests for MarkdownIntegration."""

    def test_integration_properties(self) -> None:
        """Test integration name and supported features."""
        integration = MarkdownIntegration()
        assert integration.integration_name == "markdown"
        assert "create_ticket" in integration.supported_features
        assert "export_markdown" in integration.supported_features

    @pytest.mark.asyncio
    async def test_initialize(self) -> None:
        """Test initialization (should be no-op)."""
        integration = MarkdownIntegration()
        await integration.initialize()
        assert integration._initialized is True

    @pytest.mark.asyncio
    async def test_create_ticket_success(
        self,
        sample_context: ConversationContext,
        sample_decision: HandoffDecision,
    ) -> None:
        """Test create_ticket returns valid HandoffResult."""
        integration = MarkdownIntegration()
        await integration.initialize()

        result = await integration.create_ticket(sample_context, sample_decision)

        assert result.success is True
        assert result.status == HandoffStatus.PENDING
        assert result.handoff_id is not None
        assert result.ticket_id == result.handoff_id
        assert result.ticket_url is None  # No external URL
        assert "markdown_content" in result.metadata
        assert result.metadata["export_format"] == "markdown"

    @pytest.mark.asyncio
    async def test_create_ticket_includes_content(
        self,
        sample_context: ConversationContext,
        sample_decision: HandoffDecision,
    ) -> None:
        """Test create_ticket markdown content is correct."""
        integration = MarkdownIntegration()

        result = await integration.create_ticket(sample_context, sample_decision)

        markdown = result.metadata["markdown_content"]
        assert "# Handoff Context: conv-test-123" in markdown
        assert "## Session Info" in markdown

    @pytest.mark.asyncio
    async def test_check_agent_availability(self) -> None:
        """Test check_agent_availability returns empty list."""
        integration = MarkdownIntegration()
        result = await integration.check_agent_availability()
        assert result == []

    @pytest.mark.asyncio
    async def test_assign_to_agent(self) -> None:
        """Test assign_to_agent returns False."""
        integration = MarkdownIntegration()
        result = await integration.assign_to_agent("ticket-123", "agent-456")
        assert result is False


# ============================================================================
# HandoffOrchestrator Integration Tests
# ============================================================================


class TestOrchestratorWithJsonMarkdown:
    """Tests for HandoffOrchestrator with json/markdown helpdesks."""

    def test_json_helpdesk_valid(self) -> None:
        """Test that 'json' is a valid helpdesk value."""
        orchestrator = HandoffOrchestrator(helpdesk="json")
        assert orchestrator.helpdesk == "json"

    def test_markdown_helpdesk_valid(self) -> None:
        """Test that 'markdown' is a valid helpdesk value."""
        orchestrator = HandoffOrchestrator(helpdesk="markdown")
        assert orchestrator.helpdesk == "markdown"

    @pytest.mark.asyncio
    async def test_json_integration_loaded(self) -> None:
        """Test that json helpdesk loads GenericIntegration."""
        orchestrator = HandoffOrchestrator(helpdesk="json")
        integration = await orchestrator._get_integration()

        assert integration is not None
        assert integration.integration_name == "json"
        assert isinstance(integration, GenericIntegration)

    @pytest.mark.asyncio
    async def test_markdown_integration_loaded(self) -> None:
        """Test that markdown helpdesk loads MarkdownIntegration."""
        orchestrator = HandoffOrchestrator(helpdesk="markdown")
        integration = await orchestrator._get_integration()

        assert integration is not None
        assert integration.integration_name == "markdown"
        assert isinstance(integration, MarkdownIntegration)

    @pytest.mark.asyncio
    async def test_create_handoff_with_json(self, sample_messages: list[Message]) -> None:
        """Test create_handoff works with json helpdesk."""
        orchestrator = HandoffOrchestrator(helpdesk="json")

        result = await orchestrator.create_handoff(
            sample_messages,
            metadata={"user_id": "test-user", "channel": "web"},
        )

        assert result.success is True
        assert result.handoff_id is not None
        assert "json_content" in result.metadata

    @pytest.mark.asyncio
    async def test_create_handoff_with_markdown(
        self, sample_messages: list[Message]
    ) -> None:
        """Test create_handoff works with markdown helpdesk."""
        orchestrator = HandoffOrchestrator(helpdesk="markdown")

        result = await orchestrator.create_handoff(
            sample_messages,
            metadata={"user_id": "test-user", "channel": "web"},
        )

        assert result.success is True
        assert result.handoff_id is not None
        assert "markdown_content" in result.metadata

    @pytest.mark.asyncio
    async def test_no_external_api_calls_json(
        self, sample_messages: list[Message]
    ) -> None:
        """Verify no external API calls are made for json helpdesk."""
        orchestrator = HandoffOrchestrator(helpdesk="json")

        # Patch httpx to ensure no HTTP calls are made
        with patch("httpx.AsyncClient") as mock_client:
            result = await orchestrator.create_handoff(
                sample_messages,
                metadata={"user_id": "test-user"},
            )

            # httpx.AsyncClient should NOT be called
            mock_client.assert_not_called()

        assert result.success is True

    @pytest.mark.asyncio
    async def test_no_external_api_calls_markdown(
        self, sample_messages: list[Message]
    ) -> None:
        """Verify no external API calls are made for markdown helpdesk."""
        orchestrator = HandoffOrchestrator(helpdesk="markdown")

        # Patch httpx to ensure no HTTP calls are made
        with patch("httpx.AsyncClient") as mock_client:
            result = await orchestrator.create_handoff(
                sample_messages,
                metadata={"user_id": "test-user"},
            )

            # httpx.AsyncClient should NOT be called
            mock_client.assert_not_called()

        assert result.success is True
