"""Tests for API key authentication."""

import pytest
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from handoffkit.api.app import create_app
# These imports will fail until implemented, which is part of the Red phase
try:
    from handoffkit.api.auth import get_api_key, hash_key, verify_key
    from handoffkit.api.models.auth import APIKey
except ImportError:
    pass

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    return session

@pytest.fixture
def app(mock_db_session):
    """Create test FastAPI application with mocked dependencies."""
    with patch("handoffkit.api.app.get_api_settings") as mock_settings:
        mock_settings.return_value.is_development = True
        mock_settings.return_value.cors_origins_list = ["*"]
        mock_settings.return_value.debug = True

        # Patch storage to avoid side effects
        with patch("handoffkit.api.routes.handoff.get_handoff_storage"):
            # Patch get_db to return our mock session
            # Note: We haven't implemented get_db yet, so this might need adjustment
            with patch("handoffkit.api.auth.get_db", return_value=iter([mock_db_session])):
                app = create_app()
                yield app

@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)

class TestAPIKeyAuth:
    """Test API key authentication."""

    def test_key_hashing(self):
        """Test key hashing and verification."""
        # This test verifies the utility functions
        from handoffkit.api.auth import hash_key, verify_key, generate_api_key

        raw_key = generate_api_key()
        assert raw_key.startswith("hk_")

        hashed = hash_key(raw_key)
        assert hashed != raw_key
        assert verify_key(raw_key, hashed) is True
        assert verify_key("wrong_key", hashed) is False

    def test_valid_api_key_endpoint(self, client, mock_db_session):
        """Test accessing a protected endpoint with a valid API key."""
        # Setup
        from handoffkit.api.auth import hash_key
        from handoffkit.api.models.auth import APIKey

        raw_key = "hk_validkey123"
        hashed = hash_key(raw_key)

        # Mock DB finding the key
        api_key_obj = APIKey(
            id=str(uuid.uuid4()),
            key_hash=hashed,
            name="Test Key",
            is_active=True
        )

        # Configure mock to return our key when queried
        # This assumes the implementation will query by key_hash
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = api_key_obj

        # Patch the get_api_key dependency internals if needed,
        # but ideally we want to test the full flow.
        # However, since we are mocking the DB session inside the dependency (via get_db),
        # we need to ensure the app uses our mocked dependency logic.
        # For this test, we'll assume the client hits the endpoint and the app
        # resolves dependencies correctly.

        # We need to mock the authentication verification flow in the app
        # or rely on the mocked DB session if we can inject it.
        # Since dependency injection in tests can be tricky without overrides:

        with patch("handoffkit.api.auth.verify_api_key_in_db", return_value=api_key_obj):
             response = client.post(
                "/api/v1/check",
                headers={"Authorization": f"Bearer {raw_key}"},
                json={
                    "conversation_id": "test",
                    "user_id": "user",
                    "messages": [{"content": "hi", "speaker": "user"}]
                }
            )

        # Should be 200 (OK) because auth passed
        # Note: might fail with 500 if other parts of check endpoint fail,
        # but 401/403 is what we want to avoid.
        assert response.status_code != 401
        assert response.status_code != 403

    def test_invalid_api_key(self, client):
        """Test accessing with an invalid API key."""
        with patch("handoffkit.api.auth.verify_api_key_in_db", return_value=None):
            response = client.post(
                "/api/v1/check",
                headers={"Authorization": "Bearer hk_wrongkey"},
                json={
                    "conversation_id": "test",
                    "user_id": "user",
                    "messages": [{"content": "hi", "speaker": "user"}]
                }
            )
        assert response.status_code == 401

    def test_missing_auth_header(self, client):
        """Test accessing without auth header."""
        response = client.post(
            "/api/v1/check",
            json={
                "conversation_id": "test",
                "user_id": "user",
                "messages": [{"content": "hi", "speaker": "user"}]
            }
        )
        # HTTPBearer typically returns 403 when missing credentials (Not Authenticated),
        # but some configurations or versions might return 401 (Unauthorized).
        # We accept either as "Access Denied".
        assert response.status_code in [401, 403]

    def test_inactive_api_key(self, client):
        """Test accessing with an inactive API key."""
        from handoffkit.api.models.auth import APIKey

        api_key_obj = APIKey(
            id=str(uuid.uuid4()),
            key_hash="hash",
            name="Inactive Key",
            is_active=False
        )

        with patch("handoffkit.api.auth.verify_api_key_in_db", return_value=api_key_obj):
            response = client.post(
                "/api/v1/check",
                headers={"Authorization": "Bearer hk_inactive"},
                json={
                    "conversation_id": "test",
                    "user_id": "user",
                    "messages": [{"content": "hi", "speaker": "user"}]
                }
            )
        assert response.status_code == 403
