# Story 4-5: OpenAPI Documentation

## Story Information
**Story ID**: 4-5
**Epic**: Epic 4 - REST API & External Integration
**Status**: done
**Priority**: Medium
**Points**: 3

## Story Description

As a developer integrating HandoffKit, I want to access auto-generated API documentation, so that I can understand all endpoints without reading source code.

## Acceptance Criteria

### 1. Swagger UI Configuration
- [x] Configure Swagger UI to be served at `/api/docs` (currently defaults to `/docs`)
- [x] Configure Redoc to be served at `/api/redoc` (currently defaults to `/redoc`)
- [x] Ensure Swagger UI is accessible and functional
- [x] Ensure "Try it out" feature works for endpoints

### 2. OpenAPI Specification
- [x] Configure OpenAPI JSON spec to be served at `/api/openapi.json` (currently defaults to `/openapi.json`)
- [x] Ensure spec version is OpenAPI 3.0+
- [x] Verify spec includes all registered endpoints (`/check`, `/handoff`, `/handoff/{id}`, `/health`)
- [x] Ensure all request/response models are correctly documented with schemas

### 3. Documentation Content
- [x] Add tags/groups for endpoints (Handoff, Health, etc.)
- [x] Ensure all endpoint parameters have descriptions
- [x] Ensure all response codes (200, 4xx, 5xx) are documented
- [x] Add API title, description, and version to metadata

### 4. Testing
- [x] Test that `/api/docs` returns 200 OK and HTML content
- [x] Test that `/api/openapi.json` returns 200 OK and valid JSON
- [x] Verify JSON spec contains expected paths

## Technical Requirements

### FastAPI Configuration
Update `handoffkit/api/app.py` to set custom documentation URLs:

```python
app = FastAPI(
    title="HandoffKit API",
    description="...",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)
```

### Schema Metadata
Ensure Pydantic models and router endpoints utilize `summary`, `description`, `response_model`, and `responses` fields to populate the documentation.

**Example Endpoint Doc:**
```python
@router.post(
    "/check",
    response_model=CheckResult,
    summary="Check Handoff Recommendation",
    description="Evaluate a conversation...",
    tags=["Handoff"],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal error"}
    }
)
```

## Implementation Plan

### Phase 1: Configuration Update
1. Modify `handoffkit/api/app.py` to update `docs_url`, `redoc_url`, and `openapi_url`.
2. Verify `lifespan` and other configs remain intact.

### Phase 2: Metadata Audit
1. Review `handoffkit/api/routes/check.py`, `handoff.py`, `health.py` to ensure all endpoints have `tags`, `summary`, and `description`.
2. Review `handoffkit/api/models/` to ensure `Field` descriptions are present (already largely done, verification only).

### Phase 3: Testing
1. Create `tests/test_api_docs.py`.
2. Add tests for availability of docs endpoints.
3. Add test to validate OpenAPI schema structure.

## Test Cases

### 1. Docs Availability
```python
def test_swagger_ui_exists(client):
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()

def test_openapi_json_exists(client):
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"].startswith("3.")
```

### 2. Endpoint Documentation Presence
```python
def test_endpoints_documented(client):
    response = client.get("/api/openapi.json")
    paths = response.json()["paths"]
    assert "/api/v1/check" in paths
    assert "/api/v1/handoff" in paths
    assert "/api/v1/health" in paths
```

## Definition of Done

- [x] Swagger UI available at `/api/docs`
- [x] OpenAPI spec available at `/api/openapi.json`
- [x] All endpoints documented with correct schemas
- [x] Tests passed verifying documentation availability
- [ ] Code reviewed and approved

## Dev Agent Record

### Implementation Notes
- Updated `handoffkit/api/app.py` to configure `docs_url="/api/docs"`, `redoc_url="/api/redoc"`, and `openapi_url="/api/openapi.json"`.
- Verified that all API routes (`check`, `handoff`, `health`) have proper metadata (tags, summaries, descriptions) configured in their respective routers.
- Verified that Pydantic models in `requests.py` and `responses.py` have `Field` descriptions for schema generation.
- Created comprehensive tests in `tests/test_api_docs.py` to verify:
  - Swagger UI availability at new URL
  - Redoc availability at new URL
  - OpenAPI JSON spec availability and version
  - Presence of all key endpoints in the spec
  - Absence of docs at default URLs (security/cleanup)

### File List
- handoffkit/api/app.py
- tests/test_api_docs.py

### Change Log
- 2026-01-16: Configured custom OpenAPI documentation URLs and verified metadata coverage.
