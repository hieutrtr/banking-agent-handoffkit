"""Tests for the status endpoint and handoff storage."""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from handoffkit.api.app import create_app
from handoffkit.storage.file_storage import FileHandoffStorage, HandoffRecord


@pytest.fixture
def storage_dir():
    """Create a temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def storage(storage_dir):
    """Create file storage instance for testing."""
    return FileHandoffStorage(storage_dir)


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
def client(app, storage):
    """Create test client with mocked storage."""
    # Patch the get_handoff_storage function in the handoff route module
    with patch("handoffkit.api.routes.handoff.get_handoff_storage", return_value=storage):
        yield TestClient(app)


class TestFileHandoffStorage:
    """Test cases for FileHandoffStorage."""

    @pytest.mark.asyncio
    async def test_save_and_get_handoff(self, storage):
        """Test saving and retrieving a handoff."""
        handoff_id = "ho-test123"
        data = {
            "handoff_id": handoff_id,
            "conversation_id": "conv-123",
            "user_id": "user-456",
            "priority": "HIGH",
            "status": "pending",
            "ticket_id": "TKT-123",
            "metadata": {"channel": "web"}
        }

        # Save handoff
        await storage.save(handoff_id, data)

        # Retrieve handoff
        result = await storage.get(handoff_id)

        assert result is not None
        assert result["handoff_id"] == handoff_id
        assert result["conversation_id"] == "conv-123"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_nonexistent_handoff(self, storage):
        """Test getting a handoff that doesn't exist."""
        result = await storage.get("ho-nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_status(self, storage):
        """Test updating handoff status."""
        handoff_id = "ho-update-test"
        data = {
            "handoff_id": handoff_id,
            "conversation_id": "conv-123",
            "user_id": "user-456",
            "priority": "HIGH",
            "status": "pending"
        }

        await storage.save(handoff_id, data)

        # Update status
        updated = await storage.update_status(handoff_id, "in_progress")

        assert updated is True

        # Verify update
        result = await storage.get(handoff_id)
        assert result["status"] == "in_progress"
        assert "history" in result
        assert len(result["history"]) == 2

    @pytest.mark.asyncio
    async def test_update_nonexistent_handoff(self, storage):
        """Test updating status of nonexistent handoff."""
        updated = await storage.update_status("ho-nonexistent", "in_progress")
        assert updated is False

    @pytest.mark.asyncio
    async def test_list_by_conversation(self, storage):
        """Test listing handoffs by conversation."""
        # Save multiple handoffs for same conversation
        for i in range(3):
            await storage.save(
                f"ho-conv1-{i}",
                {
                    "handoff_id": f"ho-conv1-{i}",
                    "conversation_id": "conv-123",
                    "user_id": f"user-{i}",
                    "priority": "MEDIUM",
                    "status": "pending"
                }
            )

        # Save handoff for different conversation
        await storage.save(
            "ho-conv2-1",
            {
                "handoff_id": "ho-conv2-1",
                "conversation_id": "conv-456",
                "user_id": "user-other",
                "priority": "MEDIUM",
                "status": "pending"
            }
        )

        # List by conversation
        results = await storage.list_by_conversation("conv-123")

        assert len(results) == 3
        for r in results:
            assert r["conversation_id"] == "conv-123"

    @pytest.mark.asyncio
    async def test_list_all(self, storage):
        """Test listing all handoffs with pagination."""
        # Save multiple handoffs
        for i in range(5):
            await storage.save(
                f"ho-list-{i}",
                {
                    "handoff_id": f"ho-list-{i}",
                    "conversation_id": f"conv-{i}",
                    "user_id": f"user-{i}",
                    "priority": "MEDIUM",
                    "status": "pending"
                }
            )

        # List with pagination
        page1 = await storage.list_all(limit=2, offset=0)
        page2 = await storage.list_all(limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2

        # Check total count
        total = await storage.count()
        assert total == 5

    @pytest.mark.asyncio
    async def test_delete_handoff(self, storage):
        """Test deleting a handoff."""
        handoff_id = "ho-delete-test"
        await storage.save(handoff_id, {
            "handoff_id": handoff_id,
            "conversation_id": "conv-123",
            "user_id": "user-456",
            "priority": "HIGH",
            "status": "pending"
        })

        # Delete
        deleted = await storage.delete(handoff_id)
        assert deleted is True

        # Verify deleted
        result = await storage.get(handoff_id)
        assert result is None


class TestStatusEndpoint:
    """Test cases for GET /api/v1/handoff/{handoff_id}."""

    def test_get_handoff_status_not_found(self, client):
        """Test getting status of nonexistent handoff."""
        response = client.get("/api/v1/handoff/ho-nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_handoff_status_success(self, client, storage):
        """Test getting status of existing handoff."""
        handoff_id = "ho-status-test"

        # Save a handoff
        await storage.save(handoff_id, {
            "handoff_id": handoff_id,
            "conversation_id": "conv-123",
            "user_id": "user-456",
            "priority": "HIGH",
            "status": "in_progress",
            "ticket_id": "TKT-123",
            "assigned_agent": "agent-001",
            "history": [
                {"status": "pending", "timestamp": "2024-01-01T12:00:00Z"},
                {"status": "in_progress", "timestamp": "2024-01-01T12:05:00Z"}
            ]
        })

        # Get status
        response = client.get(f"/api/v1/handoff/{handoff_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["handoff_id"] == handoff_id
        assert data["status"] == "in_progress"
        assert data["ticket_id"] == "TKT-123"
        assert data["assigned_agent"] == "agent-001"
        assert "history" in data


class TestListHandoffsEndpoint:
    """Test cases for GET /api/v1/handoff."""

    @pytest.mark.asyncio
    async def test_list_handoffs_empty(self, client, storage):
        """Test listing handoffs when none exist."""
        response = client.get("/api/v1/handoff")
        assert response.status_code == 200
        data = response.json()
        assert data["handoffs"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_handoffs_with_data(self, client, storage):
        """Test listing handoffs with data."""
        # Save some handoffs
        for i in range(3):
            await storage.save(f"ho-list-{i}", {
                "handoff_id": f"ho-list-{i}",
                "conversation_id": f"conv-{i}",
                "user_id": f"user-{i}",
                "priority": "MEDIUM",
                "status": "pending"
            })

        response = client.get("/api/v1/handoff?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["handoffs"]) == 3
        assert data["total"] == 3
        assert data["limit"] == 10
        assert data["has_next"] is False
        assert data["has_previous"] is False


class TestCancelHandoffEndpoint:
    """Test cases for DELETE /api/v1/handoff/{handoff_id}."""

    @pytest.mark.asyncio
    async def test_cancel_handoff_not_found(self, client, storage):
        """Test cancelling nonexistent handoff."""
        response = client.delete("/api/v1/handoff/ho-nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_handoff_success(self, client, storage):
        """Test cancelling existing handoff."""
        handoff_id = "ho-cancel-test"

        # Save a handoff
        await storage.save(handoff_id, {
            "handoff_id": handoff_id,
            "conversation_id": "conv-123",
            "user_id": "user-456",
            "priority": "HIGH",
            "status": "pending"
        })

        # Cancel
        response = client.delete(f"/api/v1/handoff/{handoff_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

        # Verify cancelled
        status_response = client.get(f"/api/v1/handoff/{handoff_id}")
        status_data = status_response.json()
        assert status_data["status"] == "cancelled"


class TestConversationHandoffsEndpoint:
    """Test cases for GET /api/v1/conversation/{id}/handoffs."""

    @pytest.mark.asyncio
    async def test_list_conversation_handoffs(self, client, storage):
        """Test listing handoffs for a conversation."""
        # Save handoffs for conversation
        for i in range(3):
            await storage.save(f"ho-conv-test-{i}", {
                "handoff_id": f"ho-conv-test-{i}",
                "conversation_id": "conv-test",
                "user_id": f"user-{i}",
                "priority": "MEDIUM",
                "status": "pending"
            })

        # Save handoff for different conversation
        await storage.save("ho-other-conv", {
            "handoff_id": "ho-other-conv",
            "conversation_id": "conv-other",
            "user_id": "user-other",
            "priority": "MEDIUM",
            "status": "pending"
        })

        response = client.get("/api/v1/conversation/conv-test/handoffs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        for h in data:
            assert h["conversation_id"] == "conv-test"
