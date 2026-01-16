"""Tests for rate limiting."""

import time
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient

from handoffkit.api.models.auth import APIKey

# These will be implemented
try:
    from handoffkit.api.limiter import RateLimiter, check_rate_limit
except ImportError:
    pass

class TestRateLimiterCore:
    """Test the core RateLimiter class logic."""

    def test_token_bucket_algorithm(self):
        """Test basic token bucket functionality."""
        # 10 requests per minute, capacity 5
        limiter = RateLimiter(rate_per_minute=10, burst_capacity=5)
        key = "test_key"

        # Should allow up to capacity
        for _ in range(5):
            allowed, _ = limiter.allow(key)
            assert allowed is True

        # Should reject next request (capacity used)
        allowed, wait = limiter.allow(key)
        assert allowed is False
        assert wait > 0

    def test_refill_logic(self):
        """Test that tokens refill over time."""
        # 60 requests per minute = 1 per second
        limiter = RateLimiter(rate_per_minute=60, burst_capacity=1)
        key = "refill_key"

        allowed, _ = limiter.allow(key)
        assert allowed is True

        allowed, _ = limiter.allow(key)
        assert allowed is False

        # Wait 1.1 seconds
        time.sleep(1.1)

        allowed, _ = limiter.allow(key)
        assert allowed is True

    def test_multiple_keys(self):
        """Test that limits are tracked per key."""
        limiter = RateLimiter(rate_per_minute=1, burst_capacity=1)

        allowed, _ = limiter.allow("key1")
        assert allowed is True

        allowed, _ = limiter.allow("key1")
        assert allowed is False

        # key2 should be independent
        allowed, _ = limiter.allow("key2")
        assert allowed is True


@pytest.fixture
def rate_limited_app():
    """Create a test app with rate limiting."""
    from handoffkit.api.limiter import RateLimiter, check_rate_limit
    from handoffkit.api.auth import get_api_key

    app = FastAPI()

    # Mock limiter for testing speed
    # 2 requests per minute allowed
    test_limiter = RateLimiter(rate_per_minute=2, burst_capacity=2)

    async def mock_get_api_key():
        return APIKey(id="test_api_key_123", key_hash="hash", name="Test", is_active=True)

    async def mock_check_rate_limit(api_key: APIKey = Depends(mock_get_api_key)):
        allowed, wait_time = test_limiter.allow(api_key.id)
        if not allowed:
             raise HTTPException(status_code=429, detail="Too Many Requests", headers={"Retry-After": str(wait_time)})
        return True

    @app.get("/test")
    async def test_endpoint(allowed: bool = Depends(mock_check_rate_limit)):
        return {"status": "ok"}

    return app

@pytest.fixture
def client(rate_limited_app):
    return TestClient(rate_limited_app)

class TestRateLimitIntegration:
    """Test rate limiting integration with FastAPI."""

    def test_rate_limit_enforcement(self, client):
        """Test that API returns 429 when limit exceeded."""
        # Configured for 2 requests

        # Request 1: OK
        response = client.get("/test")
        assert response.status_code == 200

        # Request 2: OK
        response = client.get("/test")
        assert response.status_code == 200

        # Request 3: 429
        response = client.get("/test")
        assert response.status_code == 429
        assert "retry-after" in response.headers
