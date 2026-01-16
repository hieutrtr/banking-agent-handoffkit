"""Rate limiting implementation using Token Bucket algorithm."""

import time
import threading
from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Request, status

from handoffkit.api.auth import get_api_key
from handoffkit.api.config import get_api_settings
from handoffkit.api.models.auth import APIKey


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate_per_minute: float, burst_capacity: int):
        """Initialize the rate limiter.

        Args:
            rate_per_minute: Number of requests allowed per minute.
            burst_capacity: Maximum number of requests allowed in a burst.
        """
        self.rate = rate_per_minute / 60.0  # tokens per second
        self.capacity = burst_capacity
        self.tokens: Dict[str, Tuple[float, float]] = {}  # key -> (tokens, last_update)
        self._lock = threading.Lock()
        self._cleanup_counter = 0
        self._cleanup_interval = 1000  # Cleanup every 1000 requests

    def _cleanup_stale_keys(self, now: float):
        """Remove keys that haven't been used in a long time."""
        # Expiration: Time to refill to full capacity + buffer
        # If it's full, we don't strictly need to store it if we assume default is full capacity
        # (which the logic does: tokens.get(key, (capacity, now)))
        expiration_seconds = (self.capacity / self.rate) + 60

        keys_to_remove = []
        for key, (_, last_update) in self.tokens.items():
            if now - last_update > expiration_seconds:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.tokens[key]

    def allow(self, key: str) -> Tuple[bool, int]:
        """Check if a request is allowed for the given key.

        Args:
            key: Unique identifier for the client (e.g., API key ID).

        Returns:
            Tuple[bool, int]: (allowed, retry_after_seconds)
        """
        now = time.time()

        with self._lock:
            # Periodic cleanup
            self._cleanup_counter += 1
            if self._cleanup_counter >= self._cleanup_interval:
                self._cleanup_stale_keys(now)
                self._cleanup_counter = 0

            # Get current state or initialize
            tokens, last_update = self.tokens.get(key, (self.capacity, now))

            # Calculate refill
            elapsed = now - last_update
            refill = elapsed * self.rate

            # Update tokens (capped at capacity)
            tokens = min(self.capacity, tokens + refill)

            # Check if we have enough tokens
            if tokens >= 1.0:
                self.tokens[key] = (tokens - 1.0, now)
                return True, 0
            else:
                # Update timestamp even if rejected to track this interaction
                self.tokens[key] = (tokens, now)

                # Calculate retry after
                # We need 1.0 token. We have `tokens`. We generate `rate` tokens/sec.
                # (1.0 - tokens) / rate
                needed = 1.0 - tokens
                wait_time = needed / self.rate
                return False, int(wait_time) + 1


# Global rate limiter instance
_limiter_instance = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _limiter_instance
    if _limiter_instance is None:
        settings = get_api_settings()
        _limiter_instance = RateLimiter(
            rate_per_minute=settings.rate_limit_per_minute,
            burst_capacity=settings.burst_allowance
        )
    return _limiter_instance


async def check_rate_limit(
    request: Request,
    api_key: APIKey = Depends(get_api_key)
) -> bool:
    """FastAPI dependency to check rate limits.

    Note: This uses an in-memory rate limiter which is process-local.
    If running with multiple workers (e.g. gunicorn/uvicorn workers),
    the effective rate limit will be multiplied by the number of workers.
    For strict global rate limiting, a Redis-backed solution is recommended.

    Args:
        request: The incoming request.
        api_key: The authenticated API key.

    Raises:
        HTTPException: If rate limit is exceeded.
    """
    limiter = get_rate_limiter()

    allowed, wait_time = limiter.allow(api_key.id)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests",
            headers={"Retry-After": str(wait_time)}
        )

    return True
