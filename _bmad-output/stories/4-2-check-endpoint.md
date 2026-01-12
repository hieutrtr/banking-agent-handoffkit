# Story 4-2: Check Endpoint - POST /api/v1/check

## Story Information
**Story ID**: 4-2
**Epic**: Epic 4 - REST API & External Integration
**Status**: ready-for-dev
**Priority**: High
**Points**: 8

## Story Description

As a developer integrating HandoffKit into my application, I want to be able to check if a conversation should be handed off to a human agent via a simple API call, so that I can make informed decisions about routing conversations.

## Acceptance Criteria

### 1. Check Endpoint Implementation
- [ ] Create POST /api/v1/check endpoint
- [ ] Accept conversation context (messages, metadata, user info)
- [ ] Call HandoffOrchestrator.should_handoff()
- [ ] Return structured check result with confidence and reason

### 2. Request Handling
- [ ] Validate conversation messages are not empty
- [ ] Validate conversation_id and user_id are provided
- [ ] Handle missing or invalid metadata gracefully
- [ ] Support both JSON and form data inputs

### 3. Response Format
- [ ] Return should_handoff (boolean)
- [ ] Include confidence score (0.0-1.0)
- [ ] Provide human-readable reason
- [ ] Include trigger_type if handoff recommended
- [ ] Include trigger_confidence
- [ ] Add request_id for tracking

### 4. Error Handling
- [ ] Return 400 for invalid requests
- [ ] Return 500 for internal errors
- [ ] Log errors with request_id
- [ ] Return consistent error format

### 5. Performance
- [ ] Response time < 500ms for typical requests
- [ ] Support concurrent requests
- [ ] Add timeout handling

### 6. Testing
- [ ] Unit tests for endpoint
- [ ] Integration tests with mock orchestrator
- [ ] Performance tests
- [ ] Error handling tests

## Technical Requirements

### Endpoint Signature
```python
@router.post("/api/v1/check", response_model=CheckResult)
async def check_handoff(request: CheckHandoffRequest) -> CheckResult:
    """Check if a conversation should be handed off to a human."""
```

### Request Model
```python
class CheckHandoffRequest(BaseModel):
    conversation_id: str
    user_id: str
    messages: List[ConversationMessage]
    metadata: Dict[str, Any] = {}
    context: Optional[Dict[str, Any]] = None
```

### Response Model
```python
class CheckResult(BaseModel):
    should_handoff: bool
    confidence: float
    reason: str
    trigger_type: Optional[str] = None
    trigger_confidence: Optional[float] = None
    metadata: Dict[str, Any] = {}
```

### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/check" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "user_id": "user-456",
    "messages": [
      {"content": "I need help", "speaker": "user"},
      {"content": "How can I assist?", "speaker": "ai"}
    ],
    "metadata": {"channel": "web"}
  }'
```

### Example Response
```json
{
  "should_handoff": true,
  "confidence": 0.85,
  "reason": "Critical keyword detected",
  "trigger_type": "keyword_match",
  "trigger_confidence": 0.9,
  "metadata": {
    "matched_keyword": "urgent"
  }
}
```

## Implementation Plan

### Phase 1: Endpoint Setup
1. Create check router in handoffkit/api/routes/
2. Define request/response models (already in models/)
3. Implement endpoint function
4. Register router in main app

### Phase 2: Business Logic
1. Convert API models to SDK types
2. Call HandoffOrchestrator.should_handoff()
3. Convert SDK result to API response
4. Handle exceptions

### Phase 3: Testing
1. Write unit tests for request validation
2. Write integration tests with mock orchestrator
3. Test error scenarios
4. Performance testing

## Test Cases

### 1. Successful Check
```python
def test_check_handoff_success(client, mock_orchestrator):
    response = client.post("/api/v1/check", json={
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [
            {"content": "I need urgent help!", "speaker": "user"}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert "should_handoff" in data
    assert "confidence" in data
```

### 2. Invalid Request
```python
def test_check_handoff_invalid_request(client):
    response = client.post("/api/v1/check", json={
        "conversation_id": "conv-123"
        # Missing required fields
    })
    assert response.status_code == 422
```

### 3. Empty Messages
```python
def test_check_handoff_empty_messages(client):
    response = client.post("/api/v1/check", json={
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": []
    })
    assert response.status_code == 422
```

### 4. Internal Error
```python
def test_check_handoff_internal_error(client, mock_orchestrator_error):
    response = client.post("/api/v1/check", json={
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [{"content": "test", "speaker": "user"}]
    })
    assert response.status_code == 500
```

## Definition of Done

- [ ] Endpoint returns correct response format
- [ ] All acceptance criteria met
- [ ] Unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] Error handling works correctly
- [ ] Performance requirements met (<500ms)
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] API documentation auto-generated at /docs

## Story Notes

This endpoint is the primary way developers will integrate HandoffKit into their applications. It should be fast, reliable, and provide clear feedback about handoff decisions.

The endpoint should be stateless and not create any handoff records - it only provides recommendations. Use the POST /api/v1/handoff endpoint (Story 4-3) to create actual handoffs.