# Story 3.6: Intercom Integration Adapter

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer using Intercom**,
I want to **create conversations with conversation context**,
So that **handoffs work with my Intercom setup**.

## Acceptance Criteria

1. **Given** Intercom credentials configured (app_id, access_token) **When** `create_handoff(helpdesk="intercom")` is called **Then** an Intercom conversation is created **And** conversation history is formatted as markdown **And** priority is set according to mapping **And** conversation URL is returned in HandoffResult

2. **Given** test connection is requested **When** credentials are validated **Then** a test API call confirms connectivity **And** result (success/failure) is returned with helpful message

## Tasks / Subtasks

- [x] Task 1: Implement IntercomIntegration.initialize() (AC: #1, #2)
  - [x] Subtask 1.1: Create httpx AsyncClient with Bearer token auth
  - [x] Subtask 1.2: Validate credentials by calling GET /me endpoint
  - [x] Subtask 1.3: Store authenticated client for reuse
  - [x] Subtask 1.4: Add structured logging with get_logger("integrations.intercom")

- [x] Task 2: Implement create_ticket() (AC: #1)
  - [x] Subtask 2.1: Map HandoffDecision priority to Intercom priority (not_prioritized, low, medium, high, urgent)
  - [x] Subtask 2.2: Create or find contact by user_id/email
  - [x] Subtask 2.3: Create conversation via POST /conversations endpoint
  - [x] Subtask 2.4: Add handoff context as admin note (markdown formatted)
  - [x] Subtask 2.5: Parse response and construct HandoffResult with conversation_url
  - [x] Subtask 2.6: Handle API errors gracefully and return failed status

- [x] Task 3: Implement _format_conversation_note() helper (AC: #1)
  - [x] Subtask 3.1: Create markdown-formatted note with sections
  - [x] Subtask 3.2: Include: Summary, Trigger Reason, Conversation History, Extracted Entities, Metadata
  - [x] Subtask 3.3: Format conversation as speaker-labeled messages with timestamps
  - [x] Subtask 3.4: Respect Intercom character limits (10KB for notes)

- [x] Task 4: Add error handling and retry logic (AC: #1)
  - [x] Subtask 4.1: Handle HTTP 401 (authentication errors) with clear messages
  - [x] Subtask 4.2: Handle HTTP 429 (rate limiting) with retry-after header
  - [x] Subtask 4.3: Handle HTTP 4xx validation errors with details
  - [x] Subtask 4.4: Handle network errors gracefully
  - [x] Subtask 4.5: Queue failed handoffs for retry (store in memory for MVP)

- [x] Task 5: Add test_connection() method (AC: #2)
  - [x] Subtask 5.1: Implement test_connection() returning (success: bool, message: str)
  - [x] Subtask 5.2: Call GET /me to validate credentials
  - [x] Subtask 5.3: Return helpful error messages for common failures

- [x] Task 6: Integrate with HandoffOrchestrator (AC: #1)
  - [x] Subtask 6.1: Add intercom integration loading when helpdesk="intercom"
  - [x] Subtask 6.2: Pass IntercomConfig from HandoffConfig.integration.extra
  - [x] Subtask 6.3: Ensure lazy initialization of integration

- [x] Task 7: Add IntercomConfig to configuration (AC: #1, #2)
  - [x] Subtask 7.1: Create IntercomConfig model in handoffkit/integrations/intercom/config.py
  - [x] Subtask 7.2: Fields: access_token (str, excluded from repr), app_id (Optional[str])
  - [x] Subtask 7.3: Support loading from environment variables (INTERCOM_ACCESS_TOKEN, INTERCOM_APP_ID)

- [x] Task 8: Create comprehensive tests (AC: #1, #2)
  - [x] Subtask 8.1: Create tests/test_intercom_integration.py
  - [x] Subtask 8.2: Test initialization with valid credentials (mock API)
  - [x] Subtask 8.3: Test conversation creation with full context (mock API)
  - [x] Subtask 8.4: Test priority mapping (all combinations)
  - [x] Subtask 8.5: Test error handling (401, 429, 5xx, network errors)
  - [x] Subtask 8.6: Test conversation note formatting
  - [x] Subtask 8.7: Test HandoffOrchestrator integration
  - [x] Subtask 8.8: Test test_connection() method
  - [x] Subtask 8.9: Run all tests to verify no regressions

- [x] Task 9: Update exports (AC: #1)
  - [x] Subtask 9.1: Export IntercomIntegration from handoffkit.integrations
  - [x] Subtask 9.2: Export IntercomConfig from handoffkit.integrations.intercom

## Dev Notes

### Existing Code Context

From Story 3.5 (Zendesk - just completed):
- `ZendeskIntegration` provides the pattern for helpdesk integrations
- `BaseIntegration` abstract class defines the interface
- `HandoffOrchestrator.create_handoff()` is async and lazy-initializes integrations
- `HandoffStatus.FAILED` enum value exists for error cases
- All 673 tests currently passing

Existing `IntercomIntegration` stub in `handoffkit/integrations/intercom/client.py`:
- Has `__init__` accepting access_token, app_id (optional)
- All methods raise NotImplementedError
- Inherits from `BaseIntegration` abstract class
- Properties: integration_name="intercom", supported_features list
- Extra method: `add_note()` for internal notes (Intercom-specific)

`BaseIntegration` abstract class (`handoffkit/integrations/base.py`):
- Abstract methods: initialize(), create_ticket(), check_agent_availability(), assign_to_agent()
- Default implementation for get_ticket_status() and close()

### Architecture Reference

**Intercom API** (from docs):
- Base URL: `https://api.intercom.io`
- Auth: Bearer token in Authorization header
- API Version: Use `Intercom-Version: 2.11` header
- Conversation creation: POST /conversations
- Admin notes: POST /conversations/{id}/parts
- Contact lookup: POST /contacts/search
- Credential validation: GET /me

**Priority Mapping** (Intercom uses conversation priority):
| HandoffKit Priority | Intercom Priority |
|---------------------|-------------------|
| urgent | priority (SLA based) |
| high | priority |
| medium | not_prioritized |
| low | not_prioritized |

**Note:** Intercom's priority system is simpler than Zendesk. We'll use conversation attributes for urgency.

### Implementation Strategy

**IntercomIntegration.initialize():**
```python
import httpx

async def initialize(self) -> None:
    """Initialize HTTP client and validate credentials."""
    self._client = httpx.AsyncClient(
        base_url=self._base_url,
        headers={
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Intercom-Version": "2.11",
        },
        timeout=30.0,
    )

    # Validate credentials by calling /me
    response = await self._client.get("/me")
    response.raise_for_status()

    data = response.json()
    self._app = data.get("app", {})
    self._initialized = True
    logger.info(f"Intercom authenticated for app: {self._app.get('name', 'unknown')}")
```

**create_ticket() Implementation:**
```python
async def create_ticket(
    self,
    context: ConversationContext,
    decision: HandoffDecision,
) -> HandoffResult:
    """Create an Intercom conversation for handoff."""
    try:
        # Find or create contact
        contact = await self._find_or_create_contact(context)

        # Create conversation
        conversation_body = self._format_initial_message(context, decision)

        payload = {
            "from": {
                "type": "user",
                "id": contact["id"],
            },
            "body": conversation_body,
        }

        response = await self._client.post("/conversations", json=payload)
        response.raise_for_status()

        data = response.json()
        conversation = data.get("conversation", data)
        conversation_id = conversation["id"]

        # Add detailed handoff note for agents
        await self._add_handoff_note(conversation_id, context, decision)

        conversation_url = f"https://app.intercom.com/a/inbox/{self._app_id}/inbox/conversation/{conversation_id}"

        return HandoffResult(
            success=True,
            handoff_id=str(uuid.uuid4()),
            status=HandoffStatus.PENDING,
            ticket_id=conversation_id,
            ticket_url=conversation_url,
            metadata={"intercom_conversation": conversation},
        )

    except httpx.HTTPStatusError as e:
        error_msg = self._handle_http_error(e)
        logger.error(f"Intercom API error: {error_msg}")

        # Queue for retry if transient
        if e.response.status_code in (429, 500, 502, 503, 504):
            self._queue_for_retry(context, decision, error_msg)

        return HandoffResult(
            success=False,
            status=HandoffStatus.FAILED,
            error_message=error_msg,
        )
```

**Contact Lookup:**
```python
async def _find_or_create_contact(
    self,
    context: ConversationContext,
) -> dict[str, Any]:
    """Find existing contact or create new one."""
    user_email = context.metadata.get("user_email")
    user_id = context.user_id or context.metadata.get("user_id")

    # Search by external_id first
    if user_id:
        search_payload = {
            "query": {
                "field": "external_id",
                "operator": "=",
                "value": user_id,
            }
        }
        response = await self._client.post("/contacts/search", json=search_payload)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return data["data"][0]

    # Search by email
    if user_email:
        search_payload = {
            "query": {
                "field": "email",
                "operator": "=",
                "value": user_email,
            }
        }
        response = await self._client.post("/contacts/search", json=search_payload)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return data["data"][0]

    # Create new contact
    create_payload = {
        "role": "user",
        "external_id": user_id or f"handoff-{uuid.uuid4()}",
    }
    if user_email:
        create_payload["email"] = user_email

    response = await self._client.post("/contacts", json=create_payload)
    response.raise_for_status()
    return response.json()
```

### Git Intelligence (Recent Commits)

```
53193c6 fix(3-4): code review - fix template format and test coverage
42b067b feat(3-5): implement Zendesk integration adapter with code review fixes
0053802 chore(2-9): mark story as done
fe30bc1 feat(2-9): implement cloud LLM integration with code review fixes
1e87e65 feat(3-4): implement conversation summarization with code review fixes
```

**Established Patterns:**
- Commit format: `feat(X-Y): implement <description>`
- Async/await for all I/O operations
- httpx.AsyncClient for HTTP requests
- Graceful error handling (never raise, return failed HandoffResult)
- Structured logging with get_logger()
- Comprehensive mock-based tests with pytest
- Use HandoffStatus.FAILED for all error cases
- Retry queue (deque with maxlen=100) for transient errors

### Previous Story Learnings (from 3.5 Zendesk)

**Working Patterns:**
- Late import in HandoffOrchestrator to avoid circular deps
- Config model with `from_env()` class method for environment variables
- `to_integration_kwargs()` method on config for clean initialization
- Priority mapping as class constant dict
- Separate _format methods for ticket/note body
- _handle_http_error method for user-friendly messages
- _queue_for_retry for transient errors (429, 5xx, network)
- test_connection() for credential validation
- Optimized truncation (single encode/decode)
- Track added_keys to avoid duplicate metadata entries

**Code Review Issues Found in 3.5 (avoid these):**
- Use HandoffStatus.FAILED on errors, not PENDING
- Document breaking changes in story file
- Include all modified test files in File List
- Return error dict from get_ticket_status(), don't raise
- Avoid duplicate keys in formatted output

### Key Technical Considerations

1. **Intercom Authentication:**
   - Bearer token: Include in Authorization header as `Bearer {token}`
   - Access token obtained from Intercom Developer Hub
   - Include `Intercom-Version: 2.11` header for API versioning

2. **API Rate Limiting:**
   - Intercom has rate limits (varies by plan, typically 1000/minute)
   - Check for 429 response and X-RateLimit-Remaining header
   - Implement exponential backoff for retries

3. **Character Limits:**
   - Conversation messages: ~10KB per part
   - Truncate long conversations if needed
   - Use admin notes for detailed context (agents-only visibility)

4. **Contact Handling:**
   - Intercom requires a contact (user/lead) for conversations
   - Search by external_id first, then email
   - Create contact if not found
   - Use role="user" for customer contacts

5. **Conversation vs Ticket:**
   - Intercom uses "conversations" not "tickets"
   - Handoff creates a new conversation or adds to existing
   - Admin notes are internal (not visible to user)

6. **Error Handling Strategy:**
   - Never raise exceptions from create_ticket()
   - Return HandoffResult with status=FAILED and error_message
   - Log errors at WARNING/ERROR level
   - Queue for retry if transient error (429, 5xx)

7. **Testing Strategy:**
   - Mock all Intercom API calls with respx or httpx mocking
   - Test contact search/create flow
   - Test conversation creation with notes
   - Test error scenarios (401, 429, 5xx, network errors)
   - Test test_connection() method
   - Integration test with HandoffOrchestrator

### Project Structure

New files:
- `handoffkit/integrations/intercom/config.py` - IntercomConfig model

Modified files:
- `handoffkit/integrations/intercom/client.py` - Full implementation (replace stubs)
- `handoffkit/integrations/intercom/__init__.py` - Export IntercomConfig
- `handoffkit/integrations/__init__.py` - Export IntercomIntegration, IntercomConfig
- `handoffkit/core/orchestrator.py` - Add intercom integration loading
- `tests/test_intercom_integration.py` - Comprehensive tests (new file)

### Intercom API Reference

**Base URL:** `https://api.intercom.io`

**Required Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
Accept: application/json
Intercom-Version: 2.11
```

**Key Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /me | Validate credentials, get app info |
| POST | /contacts/search | Search for existing contact |
| POST | /contacts | Create new contact |
| POST | /conversations | Create new conversation |
| POST | /conversations/{id}/parts | Add message/note to conversation |

**Conversation Creation Payload:**
```json
{
  "from": {
    "type": "user",
    "id": "contact-id"
  },
  "body": "Initial message content"
}
```

**Add Admin Note Payload:**
```json
{
  "message_type": "note",
  "type": "admin",
  "admin_id": "admin-id",
  "body": "Markdown formatted handoff context"
}
```

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 3.6: Intercom Integration Adapter]
- [Source: handoffkit/integrations/base.py] - BaseIntegration abstract class
- [Source: handoffkit/integrations/intercom/client.py] - Existing stub to implement
- [Source: handoffkit/integrations/zendesk/client.py] - Pattern reference (570 lines)
- [Source: https://developers.intercom.com/docs/references/rest-api/api.intercom.io/] - Intercom API Reference
- [Source: https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/] - Intercom Authentication

## Dev Agent Record

### Agent Model Used

Claude claude-opus-4-5-20250514

### Debug Log References

N/A - All tests pass

### Completion Notes List

1. Implemented full IntercomIntegration class following ZendeskIntegration patterns
2. Created IntercomConfig model with from_env() and to_integration_kwargs() methods
3. Bearer token authentication with Intercom-Version: 2.11 header
4. Contact search/creation flow: search by external_id, then email, then create new
5. Conversation creation with initial message and admin note
6. _format_conversation_note uses HTML formatting for Intercom notes (not markdown)
7. Priority mapping: urgent/high → True (prioritized), medium/low → False
8. Full error handling with retry queue for transient errors (429, 5xx, network)
9. test_connection() validates credentials via /me endpoint
10. Integrated with HandoffOrchestrator._get_integration() for lazy loading
11. 41 comprehensive tests covering all functionality
12. All 714 project tests passing

### File List

**New Files:**
- `handoffkit/integrations/intercom/config.py` - IntercomConfig Pydantic model
- `tests/test_intercom_integration.py` - Comprehensive tests (41 tests)

**Modified Files:**
- `handoffkit/integrations/intercom/client.py` - Full implementation (752 lines)
- `handoffkit/integrations/intercom/__init__.py` - Export IntercomConfig
- `handoffkit/integrations/__init__.py` - Export IntercomConfig, IntercomIntegration
- `handoffkit/core/orchestrator.py` - Add intercom integration loading in _get_integration()
