# Story 3.10: Fallback Ticket Creation

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer implementing resilient handoff systems**,
I want to **create unassigned tickets when no agents are available or assignment fails**,
So that **customer issues are still tracked and can be addressed when agents become available**.

## Acceptance Criteria

1. **Given** no agents are available **When** handoff is triggered **Then** create unassigned ticket **And** set appropriate priority **And** include fallback reason in metadata **And** notify user of queue position

2. **Given** agent assignment fails **When** fallback is triggered **Then** create unassigned ticket **And** preserve all conversation context **And** log assignment failure **And** retry assignment later

3. **Given** integration is unavailable **When** handoff is attempted **Then** create local fallback ticket **And** queue for later submission **And** provide offline ticket ID to user **And** retry every 5 minutes up to 1 hour

## Tasks / Subtasks

- [ ] Task 1: Implement unassigned ticket creation (AC: #1)
  - [ ] Subtask 1.1: Create create_unassigned_ticket() method in integrations
  - [ ] Subtask 1.2: Set ticket priority based on handoff priority
  - [ ] Subtask 1.3: Add fallback_reason to ticket metadata
  - [ ] Subtask 1.4: Include estimated wait time calculation
  - [ ] Subtask 1.5: Handle department/group assignment when available

- [ ] Task 2: Handle agent assignment failures (AC: #2)
  - [ ] Subtask 2.1: Detect assignment failures from integration APIs
  - [ ] Subtask 2.2: Convert assigned ticket to unassigned on failure
  - [ ] Subtask 2.3: Preserve all conversation context and metadata
  - [ ] Subtask 2.4: Log detailed failure information for debugging
  - [ ] Subtask 2.5: Implement retry mechanism with exponential backoff

- [ ] Task 3: Implement integration offline handling (AC: #3)
  - [ ] Subtask 3.1: Create local fallback ticket storage
  - [ ] Subtask 3.2: Queue tickets for retry when integration recovers
  - [ ] Subtask 3.3: Generate offline ticket IDs for user reference
  - [ ] Subtask 3.4: Implement retry scheduler (5min intervals, 1hr max)
  - [ ] Subtask 3.5: Handle integration recovery and backlog processing

- [ ] Task 4: Add user notification system (AC: #1, #2, #3)
  - [ ] Subtask 4.1: Create notification messages for different scenarios
  - [ ] Subtask 4.2: Include queue position when available
  - [ ] Subtask 4.3: Provide offline ticket reference numbers
  - [ ] Subtask 4.4: Add estimated response times
  - [ ] Subtask 4.5: Support multiple notification channels

- [ ] Task 5: Enhance orchestrator fallback logic (AC: #1, #2, #3)
  - [ ] Subtask 5.1: Update create_handoff() to use fallback mechanisms
  - [ ] Subtask 5.2: Implement fallback decision tree
  - [ ] Subtask 5.3: Add comprehensive fallback metadata
  - [ ] Subtask 5.4: Create fallback statistics tracking
  - [ ] Subtask 5.5: Ensure graceful degradation

- [ ] Task 6: Create fallback ticket storage (AC: #3)
  - [ ] Subtask 6.1: Design fallback ticket data structure
  - [ ] Subtask 6.2: Implement persistent storage (JSON files)
  - [ ] Subtask 6.3: Add ticket lifecycle management
  - [ ] Subtask 6.4: Implement cleanup for old fallback tickets
  - [ ] Subtask 6.5: Add fallback ticket search functionality

- [ ] Task 7: Implement retry queue management (AC: #2, #3)
  - [ ] Subtask 7.1: Create retry queue data structure
  - [ ] Subtask 7.2: Implement priority-based retry scheduling
  - [ ] Subtask 7.3: Add retry attempt tracking
  - [ ] Subtask 7.4: Handle max retry attempts exceeded
  - [ ] Subtask 7.5: Provide retry status visibility

- [ ] Task 8: Create comprehensive tests (AC: #1, #2, #3)
  - [ ] Subtask 8.1: Test unassigned ticket creation
  - [ ] Subtask 8.2: Test assignment failure handling
  - [ ] Subtask 8.3: Test integration offline scenarios
  - [ ] Subtask 8.4: Test retry queue functionality
  - [ ] Subtask 8.5: Test fallback ticket storage
  - [ ] Subtask 8.6: Test user notifications
  - [ ] Subtask 8.7: Test retry scheduling
  - [ ] Subtask 8.8: Test end-to-end fallback flows

- [ ] Task 9: Add monitoring and metrics (AC: #1, #2, #3)
  - [ ] Subtask 9.1: Track fallback ticket creation rate
  - [ ] Subtask 9.2: Monitor retry queue size
  - [ ] Subtask 9.3: Log fallback reasons statistics
  - [ ] Subtask 9.4: Track integration availability
  - [ ] Subtask 9.5: Add fallback success rate metrics

- [ ] Task 10: Update documentation and examples (AC: #1, #2, #3)
  - [ ] Subtask 10.1: Document fallback mechanisms
  - [ ] Subtask 10.2: Create configuration examples
  - [ ] Subtask 10.3: Document retry behavior
  - [ ] Subtask 10.4: Create troubleshooting guide
  - [ ] Subtask 10.5: Update API documentation

## Dev Notes

### Implementation Context

**Previous Story Learnings (from 3.9 Round Robin):**
- Established pattern: Check agent availability before assignment
- Round-robin distributes load but may still result in no agents
- Assignment failures need graceful handling
- All operations must be thread-safe for async context
- Comprehensive logging essential for debugging

**Current State of Fallback Handling:**
- Basic unassigned ticket creation exists but limited
- No sophisticated retry mechanisms
- Limited user feedback on fallback scenarios
- No offline handling when integrations are unavailable

### Technical Architecture

**Fallback Decision Tree:**
```
Handoff Request
    ↓
Check Integration Available?
    ↓ No
Create Local Fallback Ticket → Queue for Retry → Notify User (Offline)
    ↓ Yes
Check Agent Availability
    ↓ None Available
Create Unassigned Ticket → Set Priority → Notify User (Queue Position)
    ↓ Agents Available
Try Agent Assignment
    ↓ Success
Ticket Created with Agent → Log Success
    ↓ Failure
Convert to Unassigned → Log Failure → Queue for Retry → Notify User
```

**Fallback Ticket Structure:**
```python
@dataclass
class FallbackTicket:
    fallback_id: str  # Local unique ID
    handoff_id: str   # Original handoff ID
    integration_name: str
    ticket_data: dict  # Full ticket data
    fallback_reason: FallbackReason
    priority: HandoffPriority
    created_at: datetime
    retry_count: int = 0
    last_retry_at: Optional[datetime] = None
    status: FallbackStatus = FallbackStatus.PENDING
```

**Integration Enhancement:**
```python
class BaseIntegration(ABC):
    @abstractmethod
    async def create_unassigned_ticket(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
        fallback_reason: str,
    ) -> HandoffResult:
        """Create ticket without agent assignment."""

    @abstractmethod
    async def convert_to_unassigned(
        self,
        ticket_id: str,
        fallback_reason: str,
    ) -> bool:
        """Convert assigned ticket to unassigned."""

    @abstractmethod
    async def retry_assignment(
        self,
        ticket_id: str,
        agent_id: str,
    ) -> bool:
        """Retry failed agent assignment."""
```

**Local Fallback Storage:**
```python
class FallbackTicketStore:
    def __init__(self, storage_path: str = "./fallback_tickets"):
        self._storage_path = Path(storage_path)
        self._tickets: dict[str, FallbackTicket] = {}
        self._retry_queue: PriorityQueue[FallbackTicket] = PriorityQueue()

    async def store_ticket(self, ticket: FallbackTicket) -> None:
        """Store fallback ticket for later processing."""

    async def get_retry_candidates(self) -> list[FallbackTicket]:
        """Get tickets ready for retry."""

    async def update_ticket_status(self, fallback_id: str, status: FallbackStatus) -> None:
        """Update ticket status after retry."""
```

**Retry Scheduler:**
```python
class RetryScheduler:
    def __init__(self, check_interval: int = 300):  # 5 minutes
        self._check_interval = check_interval
        self._max_retries = 12  # 1 hour total
        self._running = False

    async def start(self) -> None:
        """Start background retry process."""

    async def schedule_retry(self, ticket: FallbackTicket) -> None:
        """Schedule ticket for retry."""

    def _calculate_next_retry_time(self, ticket: FallbackTicket) -> datetime:
        """Calculate next retry time with exponential backoff."""
```

**User Notification System:**
```python
class FallbackNotifier:
    def __init__(self, notification_config: NotificationConfig):
        self._config = notification_config

    async def notify_unassigned_ticket(
        self,
        handoff_result: HandoffResult,
        queue_position: Optional[int] = None,
        estimated_wait: Optional[timedelta] = None,
    ) -> None:
        """Notify user of unassigned ticket creation."""

    async def notify_offline_ticket(
        self,
        fallback_id: str,
        retry_schedule: str,
    ) -> None:
        """Notify user of offline ticket creation."""

    def _format_fallback_message(
        self,
        reason: FallbackReason,
        metadata: dict,
    ) -> str:
        """Format appropriate message based on fallback reason."""
```

**Orchestrator Enhancement:**
```python
# In HandoffOrchestrator.create_handoff()
try:
    # Existing availability check and assignment logic
    result = await self._attempt_agent_assignment(
        integration, context, decision, available_agents
    )
except IntegrationUnavailableError:
    # Integration is offline
    result = await self._create_fallback_ticket(
        integration_name=integration.integration_name,
        context=context,
        decision=decision,
        reason=FallbackReason.INTEGRATION_OFFLINE,
    )
except Exception as e:
    # Unexpected error
    result = await self._create_fallback_ticket(
        integration_name=integration.integration_name,
        context=context,
        decision=decision,
        reason=FallbackReason.UNKNOWN_ERROR,
        error_details=str(e),
    )
```

### Key Technical Considerations

1. **Storage Persistence:**
   - Use JSON files for fallback ticket storage
   - Implement atomic write operations
   - Add corruption detection and recovery
   - Support configurable storage location

2. **Retry Logic:**
   - Exponential backoff for retries
   - Maximum retry attempts (default: 12 = 1 hour)
   - Priority-based retry queue
   - Dead letter queue for failed retries

3. **Error Handling:**
   - Graceful degradation on all failures
   - Comprehensive error logging
   - User-friendly error messages
   - Circuit breaker pattern for integrations

4. **Performance:**
   - Async operations for non-blocking I/O
   - Efficient queue management
   - Minimal overhead when not in fallback
   - Batch processing for retry queue

5. **Monitoring:**
   - Metrics for fallback rate
   - Retry queue size monitoring
   - Integration health checks
   - Alert on high fallback rates

6. **Data Integrity:**
   - Preserve all conversation context
   - Maintain ticket metadata
   - Audit trail for fallback decisions
   - Consistent state management

### Implementation Strategy

**Phase 1: Core Fallback Infrastructure**
1. Create FallbackTicket and storage classes
2. Implement basic unassigned ticket creation
3. Add retry queue management
4. Write unit tests

**Phase 2: Integration Enhancements**
1. Add fallback methods to BaseIntegration
2. Implement in Zendesk and Intercom adapters
3. Add local fallback ticket creation
4. Write integration tests

**Phase 3: Orchestrator Integration**
1. Update create_handoff() with fallback logic
2. Implement retry scheduler
3. Add user notification system
4. Write end-to-end tests

**Phase 4: Monitoring & Polish**
1. Add metrics and monitoring
2. Implement circuit breaker
3. Create documentation
4. Performance optimization

### Testing Approach

**Unit Tests:**
- Fallback ticket creation and storage
- Retry queue management
- Notification message formatting
- Retry timing calculations

**Integration Tests:**
- Unassigned ticket creation via APIs
- Assignment failure handling
- Integration offline scenarios
- Retry mechanism testing

**End-to-End Tests:**
- Complete fallback flows
- Integration recovery scenarios
- User notification delivery
- Data integrity verification

### Security Considerations

- Validate fallback ticket data
- Sanitize user notifications
- Secure storage of fallback tickets
- Rate limiting for retries
- Audit trail for compliance

### Git Intelligence (Recent Commits)

```
24bdb8a feat(3-8): implement agent availability checking with caching and assignment
0978e61 chore(3-6): mark story as done
e9c5542 feat(3-6): implement Intercom integration adapter with code review fixes
53193c6 fix(3-4): code review - fix template format and test coverage
42b067b feat(3-5): implement Zendesk integration adapter with code review fixes
```

**Established Patterns:**
- Commit format: `feat(X-Y): implement <description>`
- Comprehensive test coverage required
- All tests must pass before marking done
- Thread-safe async implementation
- Extensive error handling and logging
- Configuration-driven behavior

**Previous Story Learnings (from 3.9):**
- Round-robin assignment for load distribution
- Instance-level state management
- Async/await patterns for performance
- Graceful fallback mechanisms
- Metadata tracking for debugging

### Project Structure

**Modified Files:**
- `handoffkit/core/orchestrator.py` - Enhanced with fallback logic
- `handoffkit/core/config.py` - Added fallback configuration
- `handoffkit/integrations/base.py` - Added fallback interface
- `handoffkit/integrations/zendesk/client.py` - Implement fallback methods
- `handoffkit/integrations/intercom/client.py` - Implement fallback methods

**New Files:**
- `handoffkit/core/fallback.py` - Core fallback implementation
- `handoffkit/core/fallback_storage.py` - Local ticket storage
- `handoffkit/core/retry_scheduler.py` - Retry queue management
- `handoffkit/core/fallback_notifier.py` - User notification system
- `tests/test_fallback_ticket_creation.py` - Comprehensive test suite

### References

- [Source: handoffkit/core/orchestrator.py] - Current handoff creation logic
- [Source: handoffkit/core/config.py] - Configuration management
- [Source: handoffkit/integrations/base.py] - Base integration interface
- [Story: 3-9-round-robin-agent-distribution.md] - Previous story implementation
- [Zendesk API Docs] Ticket creation: https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/
- [Intercom API Docs] Conversation creation: https://developers.intercom.com/intercom-api-reference/reference/create-a-conversation

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

**Story 3.10 Created - Ready for Development**

This story implements comprehensive fallback mechanisms to ensure customer issues are always tracked, even when:
- No agents are available
- Agent assignment fails
- Integrations are offline

The implementation provides resilient handoff handling with:
1. **Unassigned ticket creation** with proper prioritization
2. **Local fallback storage** for offline scenarios
3. **Automatic retry mechanisms** with exponential backoff
4. **User notifications** with relevant information
5. **Comprehensive monitoring** and metrics

The fallback system ensures no customer request is lost while maintaining a seamless user experience through transparent error recovery.