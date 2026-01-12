# Story 4-3: Handoff Endpoint - POST /api/v1/handoff

## Story Information
**Story ID**: 4-3
**Epic**: Epic 4 - REST API & External Integration
**Status**: ready-for-dev
**Priority**: High
**Points**: 13

## Story Description

As a developer integrating HandoffKit into my application, I want to create actual handoffs to human agents via an API call, so that conversations can be transferred to appropriate support staff with full context.

## Acceptance Criteria

### 1. Handoff Creation Endpoint
- [ ] Create POST /api/v1/handoff endpoint
- [ ] Accept conversation context and handoff parameters
- [ ] Call HandoffOrchestrator.create_handoff()
- [ ] Return handoff result with ticket/assignment info
- [ ] Support priority, metadata, and context overrides

### 2. Request Handling
- [ ] Validate conversation messages are not empty
- [ ] Validate conversation_id and user_id are provided
- [ ] Support optional priority setting
- [ ] Support skip_triggers flag for manual handoffs
- [ ] Handle missing helpdesk integration gracefully

### 3. Response Format
- [ ] Return handoff_id for tracking
- [ ] Return status (pending, in_progress, etc.)
- [ ] Include ticket_id and ticket_url if created
- [ ] Include assigned_agent if assigned
- [ ] Include assigned_queue if assigned
- [ ] Include routing_rule that was applied
- [ ] Add created_at timestamp
- [ ] Add request_id for tracking

### 4. Error Handling
- [ ] Return 400 for invalid requests
- [ ] Return 404 if conversation not found
- [ ] Return 422 if handoff creation fails
- [ ] Return 502 if helpdesk integration fails
- [ ] Return 500 for internal errors
- [ ] Log errors with request_id

### 5. Performance
- [ ] Response time < 1s for typical requests
- [ ] Support concurrent handoff creation
- [ ] Add timeout handling

### 6. Testing
- [ ] Unit tests for endpoint
- [ ] Integration tests with mock orchestrator
- [ ] Helpdesk integration tests
- [ ] Error handling tests
- [ ] Performance tests

## Technical Requirements

### Endpoint Signature
```python
@router.post("/api/v1/handoff", response_model=HandoffResponse)
async def create_handoff(request: CreateHandoffRequest) -> HandoffResponse:
    """Create a new handoff to a human agent."""
```

### Request Model
```python
class CreateHandoffRequest(BaseModel):
    conversation_id: str
    user_id: str
    messages: List[ConversationMessage]
    priority: Optional[str] = "MEDIUM"  # LOW, MEDIUM, HIGH, URGENT, CRITICAL
    metadata: Dict[str, Any] = {}
    context: Optional[Dict[str, Any]] = None
    skip_triggers: bool = False
```

### Response Model
```python
class HandoffResponse(BaseModel):
    handoff_id: str
    status: str
    conversation_id: str
    user_id: str
    priority: str
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    assigned_agent: Optional[str] = None
    assigned_queue: Optional[str] = None
    routing_rule: Optional[str] = None
    created_at: datetime
    metadata: Dict[str, Any] = {}
```

### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/handoff" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "user_id": "user-456",
    "messages": [
      {"content": "I need help with billing", "speaker": "user"},
      {"content": "Let me transfer you", "speaker": "ai"}
    ],
    "priority": "HIGH",
    "metadata": {"channel": "web", "product": "premium"}
  }'
```

### Example Response
```json
{
  "handoff_id": "ho-abc123",
  "status": "pending",
  "conversation_id": "conv-123",
  "user_id": "user-456",
  "priority": "HIGH",
  "ticket_id": "TKT-12345",
  "ticket_url": "https://helpdesk.example.com/tickets/12345",
  "assigned_agent": null,
  "assigned_queue": "billing_support",
  "routing_rule": "billing_issues",
  "created_at": "2024-01-01T12:00:00Z",
  "metadata": {}
}
```

## Implementation Plan

### Phase 1: Endpoint Setup
1. Create handoff router in handoffkit/api/routes/
2. Define request/response models (extend existing models)
3. Implement endpoint function
4. Register router in main app

### Phase 2: Business Logic
1. Convert API models to SDK types
2. Call HandoffOrchestrator.create_handoff()
3. Convert SDK result to API response
4. Handle helpdesk integration
5. Handle routing rules application

### Phase 3: Testing
1. Write unit tests for request validation
2. Write integration tests with mock orchestrator
3. Test helpdesk integration
4. Test error scenarios
5. Performance testing

## Test Cases

### 1. Successful Handoff Creation
```python
def test_create_handoff_success(client, mock_orchestrator):
    response = client.post("/api/v1/handoff", json={
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [
            {"content": "I need help", "speaker": "user"},
            {"content": "Let me transfer you", "speaker": "ai"}
        ],
        "priority": "HIGH"
    })
    assert response.status_code == 200
    data = response.json()
    assert "handoff_id" in data
    assert data["status"] == "pending"
    assert "ticket_id" in data
```

### 2. Handoff with Routing Rule
```python
def test_create_handoff_with_routing(client, mock_orchestrator):
    response = client.post("/api/v1/handoff", json={
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [{"content": "billing question", "speaker": "user"}],
        "metadata": {"tier": "vip"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_queue"] == "vip_support"
    assert data["routing_rule"] == "vip_routing"
```

### 3. Invalid Request
```python
def test_create_handoff_invalid_request(client):
    response = client.post("/api/v1/handoff", json={
        "conversation_id": "conv-123"
        # Missing required fields
    })
    assert response.status_code == 422
```

### 4. Handoff Creation Failed
```python
def test_create_handoff_failed(client, mock_orchestrator_error):
    response = client.post("/api/v1/handoff", json={
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [{"content": "test", "speaker": "user"}]
    })
    assert response.status_code == 422
```

### 5. Helpdesk Integration Error
```python
def test_create_handoff_helpdesk_error(client, mock_helpdesk_error):
    response = client.post("/api/v1/handoff", json={
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [{"content": "test", "speaker": "user"}]
    })
    assert response.status_code == 502
```

### 6. Skip Triggers
```python
def test_create_handoff_skip_triggers(client, mock_orchestrator):
    response = client.post("/api/v1/handoff", json={
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "messages": [{"content": "test", "speaker": "user"}],
        "skip_triggers": True
    })
    assert response.status_code == 200
```

## Definition of Done

- [ ] Endpoint returns correct response format
- [ ] All acceptance criteria met
- [ ] Unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] Helpdesk integration works correctly
- [ ] Error handling works correctly
- [ ] Performance requirements met (<1s)
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] API documentation auto-generated at /docs

## Story Notes

This endpoint creates actual handoffs and may result in helpdesk tickets being created. It should be used when you've determined that a handoff is needed (via the /api/v1/check endpoint or your own logic).

The endpoint will:
1. Create a handoff record
2. Apply routing rules (if enabled)
3. Create a helpdesk ticket (if configured)
4. Return the handoff details for tracking

For handoffs that fail to create tickets (e.g., helpdesk unavailable), the handoff will still be created with a "pending" status that can be retried later.