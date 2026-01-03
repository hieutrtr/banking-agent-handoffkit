# Story 3.5: Zendesk Integration Adapter

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer using Zendesk**,
I want to **automatically create tickets with conversation context**,
So that **handoffs appear in my existing support workflow**.

## Acceptance Criteria

1. **Given** Zendesk credentials configured (subdomain, email, API token) **When** `create_handoff(helpdesk="zendesk")` is called **Then** a Zendesk ticket is created via API **And** conversation history is added as the ticket description **And** priority is mapped (immediate→urgent, high→high, normal→normal) **And** ticket URL is returned in HandoffResult

2. **Given** Zendesk API returns an error **When** ticket creation fails **Then** error is captured in HandoffResult.error **And** status is "failed" **And** handoff is queued for retry

## Tasks / Subtasks

- [x] Task 1: Implement ZendeskIntegration.initialize() (AC: #1)
  - [x] Subtask 1.1: Create httpx AsyncClient with basic auth (email/token pattern)
  - [x] Subtask 1.2: Validate credentials by calling /api/v2/users/me.json
  - [x] Subtask 1.3: Store authenticated client for reuse
  - [x] Subtask 1.4: Add structured logging with get_logger("integrations.zendesk")

- [x] Task 2: Implement create_ticket() (AC: #1, #2)
  - [x] Subtask 2.1: Map HandoffDecision priority to Zendesk priority (immediate→urgent, high→high, normal→normal, low→low)
  - [x] Subtask 2.2: Format conversation history as ticket description (markdown)
  - [x] Subtask 2.3: Include metadata: user_id, session_id, trigger_type, summary
  - [x] Subtask 2.4: Call POST /api/v2/tickets.json with ticket payload
  - [x] Subtask 2.5: Parse response and construct HandoffResult with ticket_url
  - [x] Subtask 2.6: Handle API errors gracefully and return failed status

- [x] Task 3: Implement format_ticket_body() helper (AC: #1)
  - [x] Subtask 3.1: Create markdown-formatted ticket body with sections
  - [x] Subtask 3.2: Include: Summary, Trigger Reason, Conversation History, Extracted Entities, Metadata
  - [x] Subtask 3.3: Format conversation as speaker-labeled messages with timestamps
  - [x] Subtask 3.4: Respect Zendesk character limits (64KB for description)

- [x] Task 4: Add error handling and retry logic (AC: #2)
  - [x] Subtask 4.1: Handle HTTP 401/403 (authentication errors) with clear messages
  - [x] Subtask 4.2: Handle HTTP 429 (rate limiting) with retry-after header
  - [x] Subtask 4.3: Handle HTTP 422 (validation errors) with field details
  - [x] Subtask 4.4: Handle network errors gracefully
  - [x] Subtask 4.5: Queue failed handoffs for retry (store in memory for MVP)

- [x] Task 5: Add test_connection() method (AC: #1)
  - [x] Subtask 5.1: Implement test_connection() returning (success: bool, message: str)
  - [x] Subtask 5.2: Call /api/v2/users/me.json to validate credentials
  - [x] Subtask 5.3: Return helpful error messages for common failures

- [x] Task 6: Integrate with HandoffOrchestrator (AC: #1)
  - [x] Subtask 6.1: Add zendesk integration loading when helpdesk="zendesk"
  - [x] Subtask 6.2: Pass ZendeskConfig from HandoffConfig.helpdesk_config
  - [x] Subtask 6.3: Ensure lazy initialization of integration

- [x] Task 7: Add ZendeskConfig to configuration (AC: #1)
  - [x] Subtask 7.1: Create ZendeskConfig model in handoffkit/integrations/zendesk/config.py
  - [x] Subtask 7.2: Fields: subdomain (str), email (str), api_token (str, excluded from repr)
  - [x] Subtask 7.3: Support loading from environment variables (ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN)

- [x] Task 8: Create comprehensive tests (AC: #1, #2)
  - [x] Subtask 8.1: Create tests/test_zendesk_integration.py
  - [x] Subtask 8.2: Test initialization with valid credentials (mock API)
  - [x] Subtask 8.3: Test ticket creation with full context (mock API)
  - [x] Subtask 8.4: Test priority mapping (all combinations)
  - [x] Subtask 8.5: Test error handling (401, 403, 422, 429, network errors)
  - [x] Subtask 8.6: Test ticket body formatting
  - [x] Subtask 8.7: Test HandoffOrchestrator integration
  - [x] Subtask 8.8: Run all tests to verify no regressions

- [x] Task 9: Update exports (AC: #1)
  - [x] Subtask 9.1: Export ZendeskIntegration from handoffkit.integrations
  - [x] Subtask 9.2: Export ZendeskConfig from handoffkit.integrations.zendesk

## Dev Notes

### Existing Code Context

From Story 3.4 (just completed):
- `ConversationSummarizer` generates summaries included in handoff metadata
- `HandoffOrchestrator.create_handoff()` packages conversation context
- `ConversationContext` contains: messages, metadata, entities, summary
- All 590 tests currently passing

Existing `ZendeskIntegration` stub in `handoffkit/integrations/zendesk/client.py`:
- Has `__init__` accepting subdomain, email, api_token
- All methods raise NotImplementedError
- Inherits from `BaseIntegration` abstract class
- Properties: integration_name="zendesk", supported_features list

`BaseIntegration` abstract class (`handoffkit/integrations/base.py`):
- Abstract methods: initialize(), create_ticket(), check_agent_availability(), assign_to_agent()
- Default implementation for get_ticket_status() and close()

### Architecture Reference

**Zendesk API** (architecture.md):
- Base URL: `https://{subdomain}.zendesk.com/api/v2`
- Auth: Basic auth with `{email}/token:{api_token}`
- Ticket creation: POST /api/v2/tickets.json
- User verification: GET /api/v2/users/me.json

**Priority Mapping** (from PRD):
| HandoffKit Priority | Zendesk Priority |
|---------------------|------------------|
| immediate | urgent |
| high | high |
| normal | normal |
| low | low |

### Implementation Strategy

**ZendeskIntegration.initialize():**
```python
import httpx
import base64

async def initialize(self) -> None:
    """Initialize HTTP client and validate credentials."""
    # Zendesk API uses {email}/token:{api_token} for basic auth
    auth_string = f"{self._email}/token:{self._api_token}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()

    self._client = httpx.AsyncClient(
        base_url=self._base_url,
        headers={
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )

    # Validate credentials
    response = await self._client.get("/users/me.json")
    response.raise_for_status()
    logger.info(f"Zendesk authenticated as: {response.json()['user']['email']}")
```

**create_ticket() Implementation:**
```python
async def create_ticket(
    self,
    context: ConversationContext,
    decision: HandoffDecision,
) -> HandoffResult:
    """Create a Zendesk ticket with full conversation context."""
    try:
        priority_map = {
            "immediate": "urgent",
            "high": "high",
            "normal": "normal",
            "low": "low",
        }

        ticket_body = self._format_ticket_body(context, decision)

        payload = {
            "ticket": {
                "subject": f"Handoff: {decision.primary_trigger.trigger_type if decision.primary_trigger else 'Manual'}",
                "comment": {"body": ticket_body},
                "priority": priority_map.get(decision.priority, "normal"),
                "requester": {"email": context.metadata.get("user_email", f"user-{context.metadata.get('user_id', 'unknown')}@handoff.local")},
                "tags": ["handoffkit", decision.primary_trigger.trigger_type if decision.primary_trigger else "manual"],
            }
        }

        response = await self._client.post("/tickets.json", json=payload)
        response.raise_for_status()

        data = response.json()
        ticket = data["ticket"]

        return HandoffResult(
            handoff_id=str(ticket["id"]),
            status="created",
            ticket_url=f"https://{self._subdomain}.zendesk.com/agent/tickets/{ticket['id']}",
            created_at=datetime.now(),
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"Zendesk API error: {e.response.status_code} - {e.response.text}")
        return HandoffResult(
            handoff_id="",
            status="failed",
            error=f"Zendesk API error: {e.response.status_code}",
            created_at=datetime.now(),
        )
```

**Ticket Body Formatting:**
```python
def _format_ticket_body(
    self,
    context: ConversationContext,
    decision: HandoffDecision,
) -> str:
    """Format conversation context as Zendesk ticket body."""
    sections = []

    # Summary section
    if context.summary:
        sections.append(f"## Summary\n{context.summary}")

    # Trigger reason
    if decision.primary_trigger:
        sections.append(
            f"## Handoff Reason\n"
            f"- Type: {decision.primary_trigger.trigger_type}\n"
            f"- Confidence: {decision.primary_trigger.confidence:.0%}\n"
            f"- Reason: {decision.primary_trigger.reason}"
        )

    # Conversation history
    history_lines = ["## Conversation History"]
    for msg in context.messages[-20:]:  # Last 20 messages
        speaker = "Customer" if msg.speaker.value == "user" else "AI Assistant"
        timestamp = msg.timestamp.strftime("%H:%M:%S") if msg.timestamp else ""
        history_lines.append(f"**{speaker}** ({timestamp}): {msg.content}")
    sections.append("\n".join(history_lines))

    # Extracted entities
    if context.entities:
        entity_lines = ["## Key Information"]
        for entity in context.entities[:10]:
            entity_lines.append(f"- {entity.entity_type}: {entity.value}")
        sections.append("\n".join(entity_lines))

    # Metadata
    meta_lines = ["## Session Info"]
    for key in ["user_id", "session_id", "channel", "conversation_duration"]:
        if key in context.metadata:
            meta_lines.append(f"- {key}: {context.metadata[key]}")
    sections.append("\n".join(meta_lines))

    return "\n\n".join(sections)
```

### Git Intelligence (Recent Commits)

```
0053802 chore(2-9): mark story as done
fe30bc1 feat(2-9): implement cloud LLM integration with code review fixes
1e87e65 feat(3-4): implement conversation summarization with code review fixes
d7313a6 fix(3-2): code review - add negative duration handling and tests
a781c4f fix(3-1): code review - remove dead ContextPackager stub
```

**Established Patterns:**
- Commit format: `feat: implement Story X.Y - Title`
- Async/await for all I/O operations
- httpx.AsyncClient for HTTP requests
- Graceful error handling (never raise, return failed result)
- Structured logging with get_logger()
- Comprehensive mock-based tests

### Previous Story Learnings (from 3.4)

**Working Patterns:**
- Late import in HandoffOrchestrator to avoid circular deps
- Pydantic models with `model_dump(mode="json")` for serialization
- Structured logging with get_logger()
- Performance tracking with time.perf_counter()
- Comprehensive test coverage for edge cases

### Key Technical Considerations

1. **Zendesk Authentication:**
   - Basic auth: `{email}/token:{api_token}` base64 encoded
   - Include in Authorization header as `Basic {encoded}`
   - Token obtained from Zendesk Admin > Channels > API

2. **API Rate Limiting:**
   - Zendesk has rate limits (varies by plan)
   - Check for 429 response and Retry-After header
   - Implement exponential backoff for retries

3. **Character Limits:**
   - Ticket description: 64KB max
   - Truncate long conversations if needed
   - Preserve most recent messages (user context)

4. **Requester Handling:**
   - If user_email in metadata, use it
   - Otherwise create placeholder email from user_id
   - Zendesk requires valid email format for requester

5. **Error Handling Strategy:**
   - Never raise exceptions from create_ticket()
   - Return HandoffResult with status="failed" and error message
   - Log errors at WARNING level
   - Queue for retry if transient error

6. **Testing Strategy:**
   - Mock all Zendesk API calls with respx or httpx mocking
   - Test all priority mappings
   - Test error scenarios (401, 403, 422, 429, 5xx)
   - Test ticket body formatting
   - Integration test with HandoffOrchestrator

### Project Structure

New files:
- `handoffkit/integrations/zendesk/config.py` - ZendeskConfig model

Modified files:
- `handoffkit/integrations/zendesk/client.py` - Full implementation (replace stubs)
- `handoffkit/integrations/zendesk/__init__.py` - Export ZendeskConfig
- `handoffkit/integrations/__init__.py` - Export ZendeskIntegration, ZendeskConfig
- `handoffkit/core/orchestrator.py` - Add zendesk integration loading (BREAKING: create_handoff() is now async)
- `handoffkit/core/types.py` - Added HandoffStatus.FAILED enum value
- `tests/test_zendesk_integration.py` - Comprehensive tests (42 tests)
- `tests/test_orchestrator.py` - Updated for async create_handoff()
- `tests/test_orchestrator_integration.py` - Updated for async create_handoff()
- `tests/test_metadata_integration.py` - Updated for async create_handoff()

### Code Review Fixes Applied

The following issues were found and fixed during code review:

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| HIGH | AC#2: Status was PENDING on error, should be FAILED | Changed to HandoffStatus.FAILED, added FAILED to enum |
| HIGH | Breaking change: create_handoff() now async | Documented in Project Structure above |
| MEDIUM | 3 test files not in File List | Added to Project Structure |
| MEDIUM | Missing orchestrator integration test | Added TestOrchestratorIntegration class |
| MEDIUM | get_ticket_status() raised RuntimeError (inconsistent) | Changed to return error dict like create_ticket() |
| LOW | Duplicate user_id in Session Info | Fixed with added_keys tracking set |
| LOW | O(n^2) truncation loop | Optimized to single encode/decode |
| LOW | Missing set_integration() test | Added test_set_integration_overrides_default() |

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 3.5: Zendesk Integration Adapter]
- [Source: _bmad-output/architecture.md#3.2 Helpdesk Adapter Interface]
- [Source: handoffkit/integrations/base.py] - BaseIntegration abstract class
- [Source: handoffkit/integrations/zendesk/client.py] - Existing stub to implement
- [Source: https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/] - Zendesk Tickets API
- [Source: https://developer.zendesk.com/api-reference/ticketing/introduction/] - Zendesk API Authentication
