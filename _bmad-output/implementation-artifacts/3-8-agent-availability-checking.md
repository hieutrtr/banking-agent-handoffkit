# Story 3.8: Agent Availability Checking

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer implementing real-time routing**,
I want to **check which agents are currently available**,
So that **handoffs can be assigned immediately when possible**.

## Acceptance Criteria

1. **Given** Zendesk integration is configured **When** availability is checked **Then** list of online agents is returned **And** results are cached for 30 seconds (TTL) **And** query completes in <200ms

2. **Given** no agents are available **When** availability check returns empty **Then** fallback to ticket creation is triggered **And** user is notified of estimated response time

## Tasks / Subtasks

- [ ] Task 1: Implement Zendesk agent availability API integration (AC: #1)
  - [ ] Subtask 1.1: Research Zendesk Users API for online status
  - [ ] Subtask 1.2: Implement API call to get online agents with department filter
  - [ ] Subtask 1.3: Parse response to extract agent info (id, name, email, status)
  - [ ] Subtask 1.4: Handle pagination for large agent lists
  - [ ] Subtask 1.5: Add error handling for API failures

- [ ] Task 2: Implement Intercom teammate availability API integration (AC: #1)
  - [ ] Subtask 2.1: Research Intercom Admins/Teammates API for online status
  - [ ] Subtask 2.2: Implement API call to get available teammates
  - [ ] Subtask 2.3: Parse response to extract teammate info (id, name, email)
  - [ ] Subtask 2.4: Handle API pagination and rate limits
  - [ ] Subtask 2.5: Add comprehensive error handling

- [ ] Task 3: Add caching mechanism (AC: #1)
  - [ ] Subtask 3.1: Implement 30-second TTL cache for availability results
  - [ ] Subtask 3.2: Cache per integration instance (not global)
  - [ ] Subtask 3.3: Ensure cache is thread-safe for async operations
  - [ ] Subtask 3.4: Add cache invalidation on configuration changes

- [ ] Task 4: Optimize for performance (AC: #1)
  - [ ] Subtask 4.1: Ensure API calls complete in <200ms
  - [ ] Subtask 4.2: Implement connection pooling for HTTP clients
  - [ ] Subtask 4.3: Add request timeout handling (default 5s, configurable)
  - [ ] Subtask 4.4: Implement async/await properly for non-blocking calls

- [ ] Task 5: Handle no agents available scenario (AC: #2)
  - [ ] Subtask 5.1: Modify create_ticket() to check availability first
  - [ ] Subtask 5.2: When no agents available, create unassigned ticket
  - [ ] Subtask 5.3: Include availability status in HandoffResult metadata
  - [ ] Subtask 5.4: Add fallback reason to trigger results

- [ ] Task 6: Create comprehensive tests (AC: #1, #2)
  - [ ] Subtask 6.1: Test Zendesk availability API with mock responses
  - [ ] Subtask 6.2: Test Intercom availability API with mock responses
  - [ ] Subtask 6.3: Test caching behavior (TTL, invalidation)
  - [ ] Subtask 6.4: Test performance requirements (<200ms)
  - [ ] Subtask 6.5: Test error handling scenarios
  - [ ] Subtask 6.6: Test no agents available fallback
  - [ ] Subtask 6.7: Test department filtering
  - [ ] Subtask 6.8: Test HandoffOrchestrator integration

- [ ] Task 7: Update HandoffOrchestrator integration (AC: #1, #2)
  - [ ] Subtask 7.1: Modify create_handoff() to call check_agent_availability()
  - [ ] Subtask 7.2: Implement logic to assign to agent if available
  - [ ] Subtask 7.3: Add configuration for availability checking behavior
  - [ ] Subtask 7.4: Update exports to include new functionality

## Dev Notes

### Implementation Context

**Previous Story Learnings (from 3.7 Generic Adapters):**
- Established pattern: Late imports in orchestrator to avoid circular dependencies
- All integrations inherit from BaseIntegration with consistent interface
- Error handling with try/catch and proper logging
- Comprehensive test coverage with mock-based testing
- No external API calls for generic adapters (local storage only)

**Current State of Agent Availability:**
- All integrations (Zendesk, Intercom, Generic, Markdown) currently return empty lists
- Comments indicate "Full implementation pending (Story 3.8)"
- Placeholder implementations exist but need real API integration

### Technical Architecture

**Integration Pattern:**
```python
class ZendeskIntegration(BaseIntegration):
    async def check_agent_availability(self, department=None) -> list[dict]:
        # Call Zendesk Users API
        # Return list of online agents
        # Cache results for 30s

class IntercomIntegration(BaseIntegration):
    async def check_agent_availability(self, department=None) -> list[dict]:
        # Call Intercom Admins API
        # Return list of available teammates
        # Cache results for 30s
```

**Caching Strategy:**
- Instance-level cache (not global) to avoid cross-integration pollution
- 30-second TTL as specified in AC
- Thread-safe for async operations
- Cache key includes integration name and department filter

**API Endpoints to Use:**

**Zendesk:**
- `GET /api/v2/users.json?role=agent&query=online`
- Filter by department if provided
- Parse user fields: id, name, email, user_fields.status

**Intercom:**
- `GET /admins` (lists all teammates)
- Parse admin fields: id, name, email, away_mode_enabled
- Consider "available" if away_mode_enabled = false

**Performance Requirements:**
- API calls must complete in <200ms (AC requirement)
- Use connection pooling for HTTP clients
- Implement proper timeouts (default 5s, configurable)
- Async/await for non-blocking operations

### Key Technical Considerations

1. **API Authentication:**
   - Zendesk: Bearer token via Authorization header
   - Intercom: Bearer token with Intercom-Version header
   - Store tokens securely, never log them

2. **Error Handling:**
   - Network failures: Return empty list, log error
   - API errors (4xx/5xx): Return empty list, log specific error
   - Timeout errors: Return empty list, log timeout
   - Rate limiting: Respect Retry-After header

3. **Caching Implementation:**
   ```python
   @cached(ttl=30)
   async def check_agent_availability(self, department=None):
       # Implementation
   ```

4. **Department Filtering:**
   - Zendesk: Use user_fields.department or groups
   - Intercom: Use teams or custom attributes
   - Case-insensitive matching

5. **Agent Status Determination:**
   - Zendesk: Check custom field "status" = "online"
   - Intercom: Check away_mode_enabled = false
   - Consider time zone differences

6. **Fallback Behavior:**
   - If availability check fails → create unassigned ticket
   - If no agents available → create unassigned ticket
   - Always include availability status in metadata

### Implementation Strategy

**Phase 1: Zendesk Implementation**
1. Research exact API endpoints and parameters
2. Implement with proper error handling
3. Add caching layer
4. Write comprehensive tests

**Phase 2: Intercom Implementation**
1. Research Intercom Admins/Teammates API
2. Implement with similar patterns to Zendesk
3. Ensure consistent behavior
4. Write tests

**Phase 3: Integration Updates**
1. Update HandoffOrchestrator to use availability
2. Implement assignment logic
3. Add configuration options
4. End-to-end testing

### Testing Approach

**Unit Tests:**
- Mock API responses for both platforms
- Test caching behavior (TTL, invalidation)
- Test error scenarios (network, API errors, timeouts)
- Test department filtering
- Test performance requirements

**Integration Tests:**
- Test with HandoffOrchestrator
- Test fallback scenarios
- Test real API calls (with test credentials)

### Security Considerations

- Never log API tokens or credentials
- Use HTTPS for all API calls
- Validate department names to prevent injection
- Sanitize agent data before returning

### Performance Optimization

- Connection pooling for HTTP clients
- Async/await for non-blocking I/O
- Efficient JSON parsing
- Minimal object creation in hot paths

### Git Intelligence (Recent Commits)

```
0978e61 chore(3-6): mark story as done
e9c5542 feat(3-6): implement Intercom integration adapter with code review fixes
53193c6 fix(3-4): code review - fix template format and test coverage
42b067b feat(3-5): implement Zendesk integration adapter with code review fixes
```

**Established Patterns:**
- Commit format: `feat(X-Y): implement <description>`
- BaseIntegration pattern for all helpdesk integrations
- HandoffStatus.FAILED for error cases
- Structured logging with get_logger()
- Comprehensive mock-based tests with pytest
- All tests must pass before marking done

**Previous Story Learnings (from 3.7):**
- Late imports in HandoffOrchestrator to avoid circular deps
- Error handling with specific exception types
- Input validation with proper error messages
- Markdown escaping for special characters
- Configurable parameters with sensible defaults

### Project Structure

**Modified Files:**
- `handoffkit/integrations/zendesk/client.py` - Implement real availability check
- `handoffkit/integrations/intercom/client.py` - Implement real availability check
- `handoffkit/core/orchestrator.py` - Add availability checking logic

**New Files:**
- `tests/test_agent_availability.py` - Comprehensive test suite

### References

- [Source: handoffkit/integrations/base.py] - BaseIntegration abstract class
- [Source: handoffkit/integrations/zendesk/client.py] - Zendesk integration pattern
- [Source: handoffkit/integrations/intercom/client.py] - Intercom integration pattern
- [Zendesk API Docs] Users endpoint: https://developer.zendesk.com/api-reference/ticketing/users/users/
- [Intercom API Docs] Admins endpoint: https://developers.intercom.com/intercom-api-reference/reference/listadmins

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

✅ **Story 3.8 Implementation Complete - 2026-01-09**

**Key Accomplishments:**
1. **Zendesk Agent Availability** - Implemented full Zendesk Users API integration with:
   - 30-second TTL caching for performance
   - Department filtering support
   - Proper error handling with timeouts
   - Online status detection via custom fields

2. **Intercom Teammate Availability** - Implemented full Intercom Admins API integration with:
   - Away mode detection for availability
   - 30-second TTL caching
   - Proper error handling

3. **Orchestrator Agent Assignment** - Enhanced HandoffOrchestrator.create_handoff() to:
   - Check agent availability before creating tickets
   - Assign to first available agent when agents are online
   - Fall back to unassigned tickets when no agents available
   - Handle assignment failures gracefully
   - Add comprehensive metadata about availability status

4. **Comprehensive Testing** - Added 25 new tests covering:
   - Both Zendesk and Intercom availability APIs
   - Agent assignment success/failure scenarios
   - Caching behavior
   - Error handling
   - Performance requirements
   - Orchestrator integration

**Technical Highlights:**
- Instance-level caching to avoid cross-integration pollution
- Thread-safe async implementation
- Proper fallback handling without failing handoffs
- Comprehensive logging for debugging
- All 783 tests passing (25 new tests added)

**Files Modified:**
- Enhanced `handoffkit/integrations/zendesk/client.py` - Full availability implementation
- Enhanced `handoffkit/integrations/intercom/client.py` - Full availability implementation
- Enhanced `handoffkit/core/orchestrator.py` - Agent assignment logic
- Created comprehensive test suite with 25 tests

**Ready for Review**

### File List

**Modified Files:**
- `handoffkit/integrations/zendesk/client.py` - Implemented check_agent_availability() with API calls, caching, and error handling
- `handoffkit/integrations/intercom/client.py` - Implemented check_agent_availability() with API calls, caching, and error handling
- `handoffkit/core/orchestrator.py` - Enhanced create_handoff() with agent assignment logic and helper method
- `handoffkit/integrations/zendesk/__init__.py` - Added availability_cache_ttl parameter to constructor
- `handoffkit/integrations/intercom/__init__.py` - Added availability_cache_ttl parameter to constructor

**New Files:**
- `tests/test_agent_availability.py` - Comprehensive test suite (16 tests) for availability APIs
- `tests/test_orchestrator_agent_assignment.py` - Integration tests (9 tests) for orchestrator agent assignment