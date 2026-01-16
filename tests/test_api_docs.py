"""Tests for API documentation."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from handoffkit.api.app import create_app

@pytest.fixture
def app():
    """Create test FastAPI application."""
    # Mock settings to avoid environment variable issues
    with patch("handoffkit.api.app.get_api_settings") as mock_settings:
        mock_settings.return_value.is_development = True
        mock_settings.return_value.cors_origins_list = ["*"]
        mock_settings.return_value.debug = True

        # We need to mock get_handoff_storage for the lifespan to work without errors
        # if the tests run in an environment where storage init might fail or log weirdly
        with patch("handoffkit.api.routes.handoff.get_handoff_storage"):
            app = create_app()
            yield app

@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)

def test_swagger_ui_exists(client):
    """Test that Swagger UI is available at /api/docs."""
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()

def test_redoc_exists(client):
    """Test that Redoc is available at /api/redoc."""
    response = client.get("/api/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()

def test_openapi_json_exists(client):
    """Test that OpenAPI spec is available at /api/openapi.json."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"].startswith("3.")
    assert data["info"]["title"] == "HandoffKit API"

def test_endpoints_documented(client):
    """Test that key endpoints are present in the OpenAPI spec."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]

    # Check that our API routes are documented
    assert "/api/v1/check" in paths
    assert "/api/v1/handoff" in paths
    assert "/api/v1/handoff/{handoff_id}" in paths
    assert "/api/v1/health" in paths

def test_default_docs_disabled(client):
    """Test that default docs URLs are NOT active (we moved them)."""
    # The default locations should return 404 because we moved them
    # Note: If they return 200, it means we haven't configured the custom URLs correctly yet
    # or FastAPI is serving them at both locations (unlikely with docs_url param)
    response_docs = client.get("/docs")
    response_redoc = client.get("/redoc")
    response_openapi = client.get("/openapi.json")

    # In FastAPI, if you change the docs_url, the old one shouldn't exist
    assert response_docs.status_code == 404
    assert response_redoc.status_code == 404
    assert response_openapi.status_code == 404
