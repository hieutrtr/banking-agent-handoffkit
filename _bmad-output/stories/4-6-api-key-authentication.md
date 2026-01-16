# Story 4-6: API Key Authentication

## Story Information
**Story ID**: 4-6
**Epic**: Epic 4 - REST API & External Integration
**Status**: done
**Priority**: High
**Points**: 5

## Story Description

As an administrator managing API access, I want to secure API endpoints with API keys, so that only authorized applications can access HandoffKit.

## Acceptance Criteria

### 1. API Key Model & Storage
- [x] Create `APIKey` SQLAlchemy model (id, key_hash, name, created_at, last_used_at, is_active)
- [x] Implement secure key generation (secrets.token_urlsafe)
- [x] Implement key hashing (passlib/bcrypt) - never store raw keys (Note: Used SHA-256 for deterministic lookup efficiency for high-entropy keys)
- [x] Create migration for `api_keys` table

### 2. Authentication Dependency
- [x] Implement `get_api_key` dependency for FastAPI
- [x] Verify `Authorization: Bearer {key}` header
- [x] Hash provided key and look up in database
- [x] Check if key exists and is active
- [x] Update `last_used_at` timestamp on successful auth
- [x] Return 401 Unauthorized for missing/invalid keys
- [x] Return 403 Forbidden for inactive keys

### 3. Secure Endpoints
- [x] Apply authentication dependency to protected endpoints:
    - `POST /api/v1/check`
    - `POST /api/v1/handoff`
    - `GET /api/v1/handoff/{id}`
    - `GET /api/v1/handoff`
- [x] Ensure `GET /health` remains public
- [x] Ensure `GET /api/docs` and `/api/openapi.json` remain public (for now)

### 4. Key Management (Internal/Seed)
- [x] Create utility function to generate and print a new API key (CLI tool or script)
- [x] Ensure at least one key can be created for testing

## Technical Requirements

### Database Schema
```python
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
```

### Authentication Logic
```python
security = HTTPBearer()
# Note: Used SHA-256 instead of bcrypt for performance on high-entropy keys

async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> APIKey:
    raw_key = credentials.credentials
    # verify logic...
```

### Security Considerations
- Use `secrets` module for generation, not `random`
- Use constant-time comparison where applicable (though bcrypt handles this)
- Log authentication failures (without logging the key)

## Implementation Plan

### Phase 1: Data Layer
1. Add `passlib[bcrypt]` to dependencies (already there from dashboard extra, but ensure core has it if needed).
2. Create `APIKey` model in `handoffkit/api/models.py` (or new `auth.py` model file).
3. Generate Alembic migration.

### Phase 2: Auth Logic
1. Create `handoffkit/api/auth.py`.
2. Implement key generation, hashing, and verification functions.
3. Implement FastAPI dependency `get_api_key`.

### Phase 3: Integration
1. Update `handoffkit/api/routes/*.py` to use `Depends(get_api_key)`.
2. Create a script `scripts/create_api_key.py` to generate keys for users.

### Phase 4: Testing
1. Test auth enforcement on endpoints (valid/invalid/missing keys).
2. Test key management functions.

## Test Cases

### 1. Valid Authentication
```python
def test_valid_api_key(client, db_session):
    # Setup: Create key in DB
    key = "hk_validkey123"
    key_hash = hash_key(key)
    # ... insert into DB ...

    response = client.post(
        "/api/v1/check",
        headers={"Authorization": f"Bearer {key}"},
        json={...}
    )
    assert response.status_code == 200
```

### 2. Invalid Key
```python
def test_invalid_api_key(client):
    response = client.post(
        "/api/v1/check",
        headers={"Authorization": "Bearer hk_wrongkey"},
        json={...}
    )
    assert response.status_code == 401
```

### 3. Missing Header
```python
def test_missing_auth_header(client):
    response = client.post("/api/v1/check", json={...})
    assert response.status_code == 403 # or 401 depending on HTTPBearer behavior
```

## Definition of Done

- [x] APIKey model created and migration applied
- [x] Auth dependency implemented and working
- [x] All v1 endpoints secured
- [x] Tests passed for auth scenarios
- [x] CLI script available to generate keys

## Dev Agent Record

### Implementation Notes
- **Data Model**: Created `APIKey` model in `handoffkit/api/models/auth.py` and `handoffkit/api/database.py` for SQLite connection.
- **Migration**: Initialized Alembic and created migration `7965c7f0a8fb_create_api_keys_table.py`.
- **Auth Logic**: Implemented `handoffkit/api/auth.py`. Used `hashlib.sha256` for key hashing instead of bcrypt for performance and simplicity with high-entropy API keys (32 bytes token urlsafe). This allows deterministic lookups in the database.
- **Integration**: Updated `check.py` and `handoff.py` routes to include `Depends(get_api_key)`.
- **Scripts**: Created `scripts/create_api_key.py` for key generation.
- **Testing**: Added `tests/test_api_auth.py` covering valid/invalid keys, missing headers, and inactive keys. All tests passed.

### File List
- handoffkit/api/models/auth.py
- handoffkit/api/database.py
- handoffkit/api/auth.py
- handoffkit/api/routes/check.py
- handoffkit/api/routes/handoff.py
- tests/test_api_auth.py
- scripts/create_api_key.py
- alembic.ini
- alembic/env.py
- alembic/versions/7965c7f0a8fb_create_api_keys_table.py

### Change Log
- 2026-01-16: Implemented full API key authentication system.
