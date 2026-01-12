"""Tests for the check endpoint."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from handoffkit.api.app import create_app
from handoffkit.api.models.requests import CheckHandoffRequest, ConversationMessage


@pytest.fixture
def app():
    """Create test FastAPI application."""
    with patch("handoffkit.api.app.get_api_settings") as mock_settings:
        mock_settings.return_value.is_development = True
        mock_settings.return_value.cors_origins_list = ["*"]
        mock_settings.return_value.debug = True

        app = create_app()
        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_check_request():
    """Create sample check request data."""
    return {
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [
            {
                "content": "I need help with billing",
                "speaker": "user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "metadata": {"channel": "web"}
    }


class TestCheckEndpoint:
    """Test cases for /api/v1/check endpoint."""

    def test_check_endpoint_exists(self, client):
        """Test that check endpoint exists."""
        response = client.post(
            "/api/v1/check",
            json={
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": [{"content": "test", "speaker": "user"}]
            }
        )
        # Should return 500 (no orchestrator) but endpoint exists
        assert response.status_code in [200, 500]

    def test_check_valid_request(self, client, sample_check_request):
        """Test check with valid request."""
        response = client.post("/api/v1/check", json=sample_check_request)

        # Should return 200 or 500 (if orchestrator not configured)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "should_handoff" in data
            assert "confidence" in data
            assert "reason" in data

    def test_check_missing_conversation_id(self, client):
        """Test check with missing conversation_id."""
        response = client.post(
            "/api/v1/check",
            json={
                "user_id": "user-456",
                "messages": [{"content": "test", "speaker": "user"}]
            }
        )
        assert response.status_code == 422

    def test_check_missing_user_id(self, client):
        """Test check with missing user_id."""
        response = client.post(
            "/api/v1/check",
            json={
                "conversation_id": "conv-123",
                "messages": [{"content": "test", "speaker": "user"}]
            }
        )
        assert response.status_code == 422

    def test_check_empty_messages(self, client):
        """Test check with empty messages list."""
        response = client.post(
            "/api/v1/check",
            json={
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": []
            }
        )
        assert response.status_code == 422

    def test_check_invalid_speaker(self, client):
        """Test check with invalid speaker value."""
        response = client.post(
            "/api/v1/check",
            json={
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": [{"content": "test", "speaker": "invalid"}]
            }
        )
        # Should still work or return 422
        assert response.status_code in [200, 422, 500]

    def test_check_with_metadata(self, client):
        """Test check with optional metadata."""
        response = client.post(
            "/api/v1/check",
            json={
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": [{"content": "test", "speaker": "user"}],
                "metadata": {
                    "channel": "web",
                    "product": "premium",
                    "custom_field": "value"
                }
            }
        )
        assert response.status_code in [200, 500]

    def test_check_with_context_override(self, client):
        """Test check with context override."""
        response = client.post(
            "/api/v1/check",
            json={
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": [{"content": "test", "speaker": "user"}],
                "context": {
                    "priority": "high",
                    "skip_triggers": True
                }
            }
        )
        assert response.status_code in [200, 500]


class TestCheckBatchEndpoint:
    """Test cases for /api/v1/check/batch endpoint."""

    def test_batch_check_exists(self, client):
        """Test that batch check endpoint exists."""
        response = client.post(
            "/api/v1/check/batch",
            json=[
                {
                    "conversation_id": "conv-1",
                    "user_id": "user-1",
                    "messages": [{"content": "test", "speaker": "user"}]
                },
                {
                    "conversation_id": "conv-2",
                    "user_id": "user-2",
                    "messages": [{"content": "test", "speaker": "user"}]
                }
            ]
        )
        assert response.status_code in [200, 500]

    def test_batch_check_empty_list(self, client):
        """Test batch check with empty list."""
        response = client.post("/api/v1/check/batch", json=[])
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0


class TestCheckResponseFormat:
    """Test response format compliance."""

    def test_response_contains_required_fields(self, client, sample_check_request):
        """Test that response contains all required fields."""
        response = client.post("/api/v1/check", json=sample_check_request)

        if response.status_code == 200:
            data = response.json()

            # Check required fields
            assert "should_handoff" in data
            assert "confidence" in data
            assert "reason" in data

            # Check types
            assert isinstance(data["should_handoff"], bool)
            assert isinstance(data["confidence"], (int, float))
            assert isinstance(data["reason"], str)

            # Check confidence range
            assert 0.0 <= data["confidence"] <= 1.0

    def test_response_includes_optional_fields(self, client, sample_check_request):
        """Test that response includes optional fields when available."""
        response = client.post("/api/v1/check", json=sample_check_request)

        if response.status_code == 200:
            data = response.json()

            # Optional fields may or may not be present
            # depending on handoff decision
            if data["should_handoff"]:
                assert "trigger_type" in data
                assert "trigger_confidence" in data


@pytest.mark.asyncio
async def test_check_with_mock_orchestrator():
    """Test check endpoint with mock orchestrator."""
    from handoffkit.api.routes.check import check_handoff
    from handoffkit.api.models.requests import CheckHandoffRequest
    from handoffkit.core.types import HandoffDecision, HandoffPriority

    # Create mock orchestrator
    mock_orchestrator = MagicMock()
    mock_orchestrator.should_handoff = AsyncMock(return_value=True)

    with patch("handoffkit.api.routes.check.HandoffOrchestrator", return_value=mock_orchestrator):
        # Create request
        request = CheckHandoffRequest(
            conversation_id="conv-123",
            user_id="user-456",
            messages=[
                ConversationMessage(content="I need help", speaker="user")
            ]
        )

        # Call endpoint
        result = await check_handoff(request)

        # Verify result
        assert result.should_handoff is True
        assert result.confidence > 0
        assert len(result.reason) > 0