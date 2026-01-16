# Story 4-7: Rate Limiting

## Story Information
**Story ID**: 4-7
**Epic**: Epic 4 - REST API & External Integration
**Status**: done
**Priority**: Medium
**Points**: 5

## Story Description

As a service operator, I want to rate limit API requests, so that no single client can overwhelm the system.

## Acceptance Criteria

### 1. Rate Limiter Implementation
- [x] Implement Token Bucket algorithm (in-memory for MVP)
- [x] Support configurable rate limits (default: 100 req/min)
- [x] Support configurable burst allowance (default: 10)
- [x] Thread-safe implementation

### 2. Middleware Integration
- [x] Create FastAPI dependency or middleware for rate limiting
- [x] Apply rate limiting to all authenticated endpoints
- [x] Identify clients by API Key (from `request.state` or dependency)
- [x] Allow public endpoints (`/health`, `/docs`) to bypass limits (or have higher limits)

### 3. Response Handling
- [x] Return `429 Too Many Requests` when limit exceeded
- [x] Include `Retry-After` header indicating seconds until reset
- [x] Include `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers (optional but good practice)

### 4. Configuration
- [x] Add rate limit settings to `APISettings` in `config.py`
- [x] Allow overriding via environment variables (`HANDOFFKIT_API_RATE_LIMIT_PER_MIN`, `HANDOFFKIT_API_BURST`)

### 5. Testing
- [x] Unit tests for `RateLimiter` class
- [x] Integration tests for API endpoints verifying 429 response
- [x] Verify concurrency handling (simultaneous requests)

## Technical Requirements

### Rate Limiter Class
```python
class RateLimiter:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = {}  # {key: (tokens, last_update)}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        # Implement token bucket logic
```

### Middleware/Dependency
```python
async def check_rate_limit(
    request: Request,
    api_key: APIKey = Depends(get_api_key)
):
    # Check limit for api_key.id
    if not limiter.allow(api_key.id):
        raise HTTPException(status_code=429, detail="Too Many Requests")
```

## Implementation Plan

### Phase 1: Core Logic
1. Update `handoffkit/api/config.py` with rate limit settings.
2. Create `handoffkit/api/limiter.py` implementing the Token Bucket algorithm.

### Phase 2: Integration
1. Create `RateLimitDependency` in `limiter.py`.
2. Update `handoffkit/api/routes/*.py` or `app.py` to apply the dependency.
   - *Decision*: Applying as a global dependency on the router or app level might be cleaner, but we need to ensure it plays nice with `get_api_key`. Since `get_api_key` is already on routes, we can chain them or add a new dependency that depends on `get_api_key`.

### Phase 3: Testing
1. Create `tests/test_rate_limiter.py`.
2. Test core logic and API integration.

## Test Cases

### 1. Basic Limits
```python
def test_rate_limit_exceeded(client, valid_api_key):
    # Configure limit to 1 req/min for testing
    # Make request 1 -> 200
    # Make request 2 -> 429
```

### 2. Burst Handling
```python
def test_burst_allowance(client, valid_api_key):
    # Configure burst=5
    # Make 5 rapid requests -> All 200
    # Make 6th request -> 429
```

### 3. Headers
```python
def test_rate_limit_headers(client, valid_api_key):
    response = client.post(...)
    assert "retry-after" in response.headers
```

## Definition of Done

- [x] RateLimiter implemented and thread-safe
- [x] API endpoints return 429 when limits exceeded
- [x] Configuration exposed via env vars
- [x] Tests passing covering normal usage, bursts, and limits
- [x] Code reviewed

## Dev Agent Record

### Implementation Notes
- Implemented `RateLimiter` class using the Token Bucket algorithm in `handoffkit/api/limiter.py`.
- Added configuration for rate limits (`rate_limit_per_minute` and `burst_allowance`) in `handoffkit/api/config.py`.
- Created a FastAPI dependency `check_rate_limit` that depends on `get_api_key` to identify clients.
- Secured API endpoints in `handoffkit/api/routes/check.py` and `handoffkit/api/routes/handoff.py` with the rate limiting dependency.
- Verified functionality with unit and integration tests in `tests/test_rate_limiter.py`.
- **Review Fixes:**
  - Added periodic cleanup mechanism to `RateLimiter` to prevent memory leaks from stale keys.
  - Implemented dynamic `Retry-After` header calculation based on token refill rate.
  - Documented scaling limitations (in-memory, process-local) in the `check_rate_limit` docstring.

### File List
- handoffkit/api/config.py
- handoffkit/api/limiter.py
- handoffkit/api/routes/check.py
- handoffkit/api/routes/handoff.py
- tests/test_rate_limiter.py

### Change Log
- 2026-01-16: Implemented in-memory Token Bucket rate limiting for authenticated API endpoints.
- 2026-01-16: Applied code review fixes (cleanup logic, dynamic retry-after).
