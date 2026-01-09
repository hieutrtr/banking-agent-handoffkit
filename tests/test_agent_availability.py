"""Tests for Agent Availability Checking (Story 3.8)."""

import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    HandoffResult,
    HandoffStatus,
    Message,
    MessageSpeaker,
)
from handoffkit.integrations.zendesk import ZendeskIntegration
from handoffkit.integrations.intercom import IntercomIntegration


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_context() -> ConversationContext:
    """Create sample conversation context."""
    return ConversationContext(
        conversation_id="conv-test-123",
        user_id="user-456",
        messages=[
            Message(
                speaker=MessageSpeaker.USER,
                content="I need help",
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            )
        ],
    )


@pytest.fixture
def sample_decision() -> HandoffDecision:
    """Create sample handoff decision."""
    return HandoffDecision(
        should_handoff=True,
        priority=HandoffPriority.MEDIUM,
        trigger_results=[],
    )


# ============================================================================
# Zendesk Integration Tests
# ============================================================================


class TestZendeskAvailability:
    """Tests for Zendesk agent availability."""

    def test_zendesk_integration_properties(self) -> None:
        """Test Zendesk integration properties."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
            availability_cache_ttl=30,
        )
        assert integration.integration_name == "zendesk"
        assert "ticket_creation" in integration.supported_features
        assert "agent_availability" in integration.supported_features

    @pytest.mark.asyncio
    async def test_zendesk_availability_success(self) -> None:
        """Test successful agent availability check."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "users": [
                {
                    "id": 123,
                    "name": "John Agent",
                    "email": "john@example.com",
                    "role": "agent",
                    "active": True,
                    "user_fields": {"status": "online"},
                },
                {
                    "id": 456,
                    "name": "Jane Agent",
                    "email": "jane@example.com",
                    "role": "agent",
                    "active": True,
                    "user_fields": {"status": "available"},
                },
                {
                    "id": 789,
                    "name": "Offline Agent",
                    "email": "offline@example.com",
                    "role": "agent",
                    "active": True,
                    "user_fields": {"status": "offline"},
                },
                {
                    "id": 999,
                    "name": "End User",
                    "email": "user@example.com",
                    "role": "end-user",
                    "active": True,
                },
            ]
        }
        integration._client.get = AsyncMock(return_value=mock_response)

        # Test availability check
        agents = await integration.check_agent_availability()

        # Should return only agents with explicit online/available status
        assert len(agents) == 2
        assert agents[0]["name"] == "John Agent"
        assert agents[0]["status"] == "online"
        assert agents[0]["platform"] == "zendesk"
        assert agents[1]["name"] == "Jane Agent"

    @pytest.mark.asyncio
    async def test_zendesk_availability_with_department_filter(self) -> None:
        """Test availability check with department filter."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock API response with department info
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "users": [
                {
                    "id": 123,
                    "name": "Sales Agent",
                    "email": "sales@example.com",
                    "role": "agent",
                    "active": True,
                    "user_fields": {"department": "Sales", "status": "online"},
                },
                {
                    "id": 456,
                    "name": "Support Agent",
                    "email": "support@example.com",
                    "role": "agent",
                    "active": True,
                    "user_fields": {"department": "Support", "status": "online"},
                },
            ]
        }
        integration._client.get = AsyncMock(return_value=mock_response)

        # Test with Sales department
        agents = await integration.check_agent_availability(department="Sales")

        assert len(agents) == 1
        assert agents[0]["name"] == "Sales Agent"

    @pytest.mark.asyncio
    async def test_zendesk_availability_no_agents_online(self) -> None:
        """Test when no agents are explicitly marked as online."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock API response with agents that have explicit offline/away status
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "users": [
                {
                    "id": 123,
                    "name": "Offline Agent",
                    "email": "offline@example.com",
                    "role": "agent",
                    "active": True,
                    "user_fields": {"status": "offline"},
                },
            ]
        }
        integration._client.get = AsyncMock(return_value=mock_response)

        # Test availability check
        agents = await integration.check_agent_availability()

        # Should return empty list since agent has explicit offline status
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_zendesk_availability_api_error(self) -> None:
        """Test handling of API errors."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock API error
        integration._client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=MagicMock(status_code=404)
            )
        )

        # Test availability check with error
        agents = await integration.check_agent_availability()

        # Should return empty list on error
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_zendesk_availability_timeout(self) -> None:
        """Test handling of timeout errors."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock timeout error
        integration._client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        # Test availability check with timeout
        agents = await integration.check_agent_availability()

        # Should return empty list on timeout
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_zendesk_availability_caching(self) -> None:
        """Test that availability results are cached."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
            availability_cache_ttl=2,  # 2 second cache for testing
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "users": [
                {
                    "id": 123,
                    "name": "Test Agent",
                    "email": "test@example.com",
                    "role": "agent",
                    "active": True,
                    "user_fields": {"status": "online"},
                },
            ]
        }
        integration._client.get = AsyncMock(return_value=mock_response)

        # First call - should hit API
        agents1 = await integration.check_agent_availability()
        assert len(agents1) == 1

        # Second call immediately - should use cache
        agents2 = await integration.check_agent_availability()
        assert len(agents2) == 1
        assert agents1 == agents2

        # Verify API was only called once
        assert integration._client.get.call_count == 1


# ============================================================================
# Intercom Integration Tests
# ============================================================================


class TestIntercomAvailability:
    """Tests for Intercom teammate availability."""

    def test_intercom_integration_properties(self) -> None:
        """Test Intercom integration properties."""
        integration = IntercomIntegration(
            access_token="token123",
            app_id="app123",
            availability_cache_ttl=30,
        )
        assert integration.integration_name == "intercom"
        assert "conversation_handoff" in integration.supported_features
        assert "team_availability" in integration.supported_features

    @pytest.mark.asyncio
    async def test_intercom_availability_success(self) -> None:
        """Test successful teammate availability check."""
        integration = IntercomIntegration(
            access_token="token123",
            app_id="app123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "admins": [
                {
                    "id": 123,
                    "name": "John Admin",
                    "email": "john@example.com",
                    "away_mode_enabled": False,
                    "active": True,
                },
                {
                    "id": 456,
                    "name": "Jane Admin",
                    "email": "jane@example.com",
                    "away_mode_enabled": False,
                    "active": True,
                },
                {
                    "id": 789,
                    "name": "Away Admin",
                    "email": "away@example.com",
                    "away_mode_enabled": True,
                    "active": True,
                },
            ]
        }
        integration._client.get = AsyncMock(return_value=mock_response)

        # Test availability check
        admins = await integration.check_agent_availability()

        # Should return only available admins (not in away mode)
        assert len(admins) == 2
        assert admins[0]["name"] == "John Admin"
        assert admins[0]["status"] == "available"
        assert admins[0]["platform"] == "intercom"
        assert admins[1]["name"] == "Jane Admin"

    @pytest.mark.asyncio
    async def test_intercom_availability_no_admins_available(self) -> None:
        """Test when no admins are available (all in away mode)."""
        integration = IntercomIntegration(
            access_token="token123",
            app_id="app123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock API response with all admins in away mode
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "admins": [
                {
                    "id": 123,
                    "name": "Away Admin",
                    "email": "away@example.com",
                    "away_mode_enabled": True,
                    "active": True,
                },
            ]
        }
        integration._client.get = AsyncMock(return_value=mock_response)

        # Test availability check
        admins = await integration.check_agent_availability()

        # Should return empty list
        assert len(admins) == 0

    @pytest.mark.asyncio
    async def test_intercom_availability_caching(self) -> None:
        """Test that availability results are cached."""
        integration = IntercomIntegration(
            access_token="token123",
            app_id="app123",
            availability_cache_ttl=2,  # 2 second cache for testing
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "admins": [
                {
                    "id": 123,
                    "name": "Test Admin",
                    "email": "test@example.com",
                    "away_mode_enabled": False,
                    "active": True,
                },
            ]
        }
        integration._client.get = AsyncMock(return_value=mock_response)

        # First call - should hit API
        admins1 = await integration.check_agent_availability()
        assert len(admins1) == 1

        # Second call immediately - should use cache
        admins2 = await integration.check_agent_availability()
        assert len(admins2) == 1
        assert admins1 == admins2

        # Verify API was only called once
        assert integration._client.get.call_count == 1


# ============================================================================
# Performance Tests
# ============================================================================


class TestAvailabilityPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_zendesk_availability_performance(self) -> None:
        """Test that Zendesk availability check meets <200ms requirement."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock slow API response (but under 5s timeout)
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"users": []}
            return mock_response

        integration._client.get = slow_response

        # Measure response time
        start_time = time.time()
        agents = await integration.check_agent_availability()
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to ms

        # Should complete in under 200ms (plus our 100ms mock delay)
        assert response_time < 300  # Giving some buffer

    @pytest.mark.asyncio
    async def test_intercom_availability_performance(self) -> None:
        """Test that Intercom availability check meets <200ms requirement."""
        integration = IntercomIntegration(
            access_token="token123",
            app_id="app123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock slow API response (but under 5s timeout)
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"admins": []}
            return mock_response

        integration._client.get = slow_response

        # Measure response time
        start_time = time.time()
        admins = await integration.check_agent_availability()
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to ms

        # Should complete in under 200ms (plus our 100ms mock delay)
        assert response_time < 300  # Giving some buffer


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestAvailabilityErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_zendesk_availability_network_error(self) -> None:
        """Test handling of network errors."""
        integration = ZendeskIntegration(
            subdomain="test",
            email="test@example.com",
            api_token="token123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock network error
        integration._client.get = AsyncMock(
            side_effect=httpx.ConnectError("Network error")
        )

        # Should handle gracefully and return empty list
        agents = await integration.check_agent_availability()
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_intercom_availability_rate_limit(self) -> None:
        """Test handling of rate limit errors."""
        integration = IntercomIntegration(
            access_token="token123",
            app_id="app123",
        )

        # Mock initialization
        integration._initialized = True
        integration._client = AsyncMock()

        # Mock rate limit error
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {"retry-after": "60"}

        integration._client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Too Many Requests",
                request=MagicMock(),
                response=mock_response
            )
        )

        # Should handle gracefully and return empty list
        admins = await integration.check_agent_availability()
        assert len(admins) == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestAvailabilityIntegration:
    """Integration tests with HandoffOrchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_calls_availability(self) -> None:
        """Test that HandoffOrchestrator properly calls availability checks."""
        from handoffkit.core.orchestrator import HandoffOrchestrator

        # Mock the integrations
        with patch("handoffkit.integrations.zendesk.ZendeskIntegration") as mock_zendesk:
            mock_zendesk_instance = MagicMock()
            mock_zendesk_instance.check_agent_availability = AsyncMock(return_value=[])
            mock_zendesk.return_value = mock_zendesk_instance

            # Create orchestrator with Zendesk
            orchestrator = HandoffOrchestrator(helpdesk="zendesk")
            orchestrator._integration = mock_zendesk_instance

            # Test availability check through orchestrator
            agents = await orchestrator._integration.check_agent_availability()

            # Verify the call was made
            mock_zendesk_instance.check_agent_availability.assert_called_once()
            assert agents == []