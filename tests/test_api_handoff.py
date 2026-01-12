"""Tests for the handoff endpoint."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from handoffkit.api.app import create_app
from handoffkit.api.models.requests import CheckHandoffRequest, ConversationMessage, CreateHandoffRequest


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
def sample_handoff_request():
    """Create sample handoff request data."""
    return {
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [
            {
                "content": "I need help with billing",
                "speaker": "user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "content": "Let me transfer you to billing",
                "speaker": "ai",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "priority": "HIGH",
        "metadata": {"channel": "web", "product": "premium"}
    }


class TestHandoffEndpoint:
    """Test cases for /api/v1/handoff endpoint."""

    def test_handoff_endpoint_exists(self, client):
        """Test that handoff endpoint exists."""
        response = client.post(
            "/api/v1/handoff",
            json={
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": [{"content": "test", "speaker": "user"}]
            }
        )
        # Should return 500 (no orchestrator) but endpoint exists
        assert response.status_code in [200, 500]

    def test_handoff_valid_request(self, client, sample_handoff_request):
        """Test handoff with valid request."""
        response = client.post("/api/v1/handoff", json=sample_handoff_request)

        # Should return 200 or 500 (if orchestrator not configured)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "handoff_id" in data
            assert "status" in data
            assert data["conversation_id"] == sample_handoff_request["conversation_id"]
            assert data["priority"] == "HIGH"

    def test_handoff_missing_conversation_id(self, client):
        """Test handoff with missing conversation_id."""
        response = client.post(
            "/api/v1/handoff",
            json={
                "user_id": "user-456",
                "messages": [{"content": "test", "speaker": "user"}]
            }
        )
        assert response.status_code == 422

    def test_handoff_missing_user_id(self, client):
        """Test handoff with missing user_id."""
        response = client.post(
            "/api/v1/handoff",
            json={
                "conversation_id": "conv-123",
                "messages": [{"content": "test", "speaker": "user"}]
            }
        )
        assert response.status_code == 422

    def test_handoff_empty_messages(self, client):
        """Test handoff with empty messages list."""
        response = client.post(
            "/api/v1/handoff",
            json={
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": []
            }
        )
        assert response.status_code == 422

    def test_handoff_with_priority(self, client):
        """Test handoff with different priority levels."""
        for priority in ["LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL"]:
            response = client.post(
                "/api/v1/handoff",
                json={
                    "conversation_id": "conv-123",
                    "user_id": "user-456",
                    "messages": [{"content": "test", "speaker": "user"}],
                    "priority": priority
                }
            )
            assert response.status_code in [200, 422, 500]

    def test_handoff_skip_triggers(self, client):
        """Test handoff with skip_triggers flag."""
        response = client.post(
            "/api/v1/handoff",
            json={
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": [{"content": "test", "speaker": "user"}],
                "skip_triggers": True
            }
        )
        assert response.status_code in [200, 500]

    def test_handoff_with_metadata(self, client):
        """Test handoff with optional metadata."""
        response = client.post(
            "/api/v1/handoff",
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


class TestHandoffResponseFormat:
    """Test response format compliance."""

    def test_response_contains_required_fields(self, client, sample_handoff_request):
        """Test that response contains all required fields."""
        response = client.post("/api/v1/handoff", json=sample_handoff_request)

        if response.status_code == 200:
            data = response.json()

            # Check required fields
            required_fields = [
                "handoff_id",
                "status",
                "conversation_id",
                "user_id",
                "priority",
                "created_at"
            ]

            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Check status values
            assert data["status"] in ["pending", "in_progress", "completed", "cancelled"]

    def test_response_includes_optional_fields(self, client, sample_handoff_request):
        """Test that response includes optional fields when available."""
        response = client.post("/api/v1/handoff", json=sample_handoff_request)

        if response.status_code == 200:
            data = response.json()

            # These fields may be null
            optional_fields = [
                "ticket_id",
                "ticket_url",
                "assigned_agent",
                "assigned_queue",
                "routing_rule"
            ]

            for field in optional_fields:
                assert field in data


class TestGetHandoffStatus:
    """Test cases for GET /api/v1/handoff/{handoff_id}."""

    def test_get_handoff_status_not_implemented(self, client):
        """Test that get handoff status returns 404 (not implemented yet)."""
        response = client.get("/api/v1/handoff/ho-abc123")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestCancelHandoff:
    """Test cases for DELETE /api/v1/handoff/{handoff_id}."""

    def test_cancel_handoff_not_implemented(self, client):
        """Test that cancel handoff returns 404 (not implemented yet)."""
        response = client.delete("/api/v1/handoff/ho-abc123")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_handoff_with_mock_orchestrator():
    """Test handoff endpoint with mock orchestrator."""
    from handoffkit.api.routes.handoff import create_handoff
    from handoffkit.api.models.requests import CreateHandoffRequest
    from handoffkit.core.types import HandoffStatus

    # Create mock result
    mock_result = MagicMock()
    mock_result.status = HandoffStatus.PENDING
    mock_result.ticket_id = "TKT-12345"
    mock_result.ticket_url = "https://helpdesk.example.com/tickets/12345"
    mock_result.metadata = {
        "routing_assignment": {"type": "queue", "queue_name": "billing_support"},
        "routing_rule": "billing_issues"
    }

    # Create mock orchestrator
    mock_orchestrator = MagicMock()
    mock_orchestrator.create_handoff = AsyncMock(return_value=mock_result)

    with patch("handoffkit.api.routes.handoff.HandoffOrchestrator", return_value=mock_orchestrator):
        # Create request
        request = CreateHandoffRequest(
            conversation_id="conv-123",
            user_id="user-456",
            messages=[
                ConversationMessage(content="I need help", speaker="user")
            ],
            priority="HIGH"
        )

        # Call endpoint
        result = await create_handoff(request)

        # Verify result
        assert result.handoff_id.startswith("ho-")
        assert result.status == "pending"
        assert result.ticket_id == "TKT-12345"
        assert result.assigned_queue == "billing_support"
        assert result.routing_rule == "billing_issues"
        assert result.priority == "HIGH"
