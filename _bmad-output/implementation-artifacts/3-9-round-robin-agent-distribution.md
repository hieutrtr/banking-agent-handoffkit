# Story 3.9: Round Robin Agent Distribution

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer implementing intelligent routing**,
I want to **distribute handoffs using a round-robin algorithm across available agents**,
So that **workload is evenly distributed and no single agent is overwhelmed**.

## Acceptance Criteria

1. **Given** multiple agents are available **When** handoff is created **Then** assign to agent using round-robin algorithm **And** track assignment history **And** complete assignment in <100ms

2. **Given** agent was recently assigned a handoff **When** next handoff occurs **Then** skip that agent in round-robin rotation **And** assign to next available agent

3. **Given** round-robin assignment fails **When** fallback is triggered **Then** assign to any available agent **And** log the failure reason **And** continue round-robin sequence

## Tasks / Subtasks

- [ ] Task 1: Implement round-robin assignment algorithm (AC: #1)
  - [ ] Subtask 1.1: Create RoundRobinAssigner class with agent rotation logic
  - [ ] Subtask 1.2: Track assignment history per agent with timestamps
  - [ ] Subtask 1.3: Implement thread-safe agent selection mechanism
  - [ ] Subtask 1.4: Add configuration for rotation window (default: 5 minutes)
  - [ ] Subtask 1.5: Ensure assignment completes in <100ms

- [ ] Task 2: Integrate with availability checking (AC: #1, #2)
  - [ ] Subtask 2.1: Modify orchestrator to use round-robin after availability check
  - [ ] Subtask 2.2: Filter available agents through round-robin selector
  - [ ] Subtask 2.3: Skip agents assigned within rotation window
  - [ ] Subtask 2.4: Update assignment metadata with round-robin info
  - [ ] Subtask 2.5: Add round-robin state to integration instances

- [ ] Task 3: Implement assignment history tracking (AC: #2)
  - [ ] Subtask 3.1: Create AssignmentHistory class with circular buffer
  - [ ] Subtask 3.2: Store agent_id, timestamp, handoff_id for each assignment
  - [ ] Subtask 3.3: Implement sliding window cleanup (keep last 24 hours)
  - [ ] Subtask 3.4: Add method to check if agent was recently assigned
  - [ ] Subtask 3.5: Make history size configurable (default: 1000 entries)

- [ ] Task 4: Add fallback mechanisms (AC: #3)
  - [ ] Subtask 4.1: Implement fallback to any available agent on failure
  - [ ] Subtask 4.2: Add retry logic with exponential backoff
  - [ ] Subtask 4.3: Log round-robin failures with detailed context
  - [ ] Subtask 4.4: Ensure round-robin state remains consistent on failure
  - [ ] Subtask 4.5: Add metrics for fallback usage

- [ ] Task 5: Create configuration options (AC: #1, #2, #3)
  - [ ] Subtask 5.1: Add round_robin_enabled flag (default: true)
  - [ ] Subtask 5.2: Add rotation_window_minutes configuration
  - [ ] Subtask 5.3: Add assignment_history_size configuration
  - [ ] Subtask 5.4: Add fallback_retry_attempts configuration
  - [ ] Subtask 5.5: Update HandoffConfig with new parameters

- [ ] Task 6: Implement comprehensive tests (AC: #1, #2, #3)
  - [ ] Subtask 6.1: Test round-robin rotation with multiple agents
  - [ ] Subtask 6.2: Test agent skipping based on assignment history
  - [ ] Subtask 6.3: Test thread safety with concurrent assignments
  - [ ] Subtask 6.4: Test fallback mechanisms on assignment failure
  - [ ] Subtask 6.5: Test performance requirement (<100ms)
  - [ ] Subtask 6.6: Test configuration parameter validation
  - [ ] Subtask 6.7: Test edge cases (single agent, no agents)
  - [ ] Subtask 6.8: Test integration with orchestrator

- [ ] Task 7: Update documentation and examples (AC: #1, #2, #3)
  - [ ] Subtask 7.1: Document round-robin algorithm implementation
  - [ ] Subtask 7.2: Create usage examples for different scenarios
  - [ ] Subtask 7.3: Document configuration options
  - [ ] Subtask 7.4: Add troubleshooting guide for assignment issues
  - [ ] Subtask 7.5: Update API documentation

## Dev Notes

### Implementation Context

**Previous Story Learnings (from 3.8 Agent Availability):**
- Established pattern: Check agent availability before assignment
- Instance-level caching for performance (30-second TTL)
- Comprehensive error handling with fallback to unassigned tickets
- All tests must pass before marking done
- Metadata tracking for debugging and monitoring

**Current State of Agent Assignment:**
- Orchestrator currently assigns to first available agent
- No load balancing or distribution logic
- Assignment is immediate without considering agent workload
- Need intelligent distribution to prevent agent overload

### Technical Architecture

**Round Robin Implementation:**
```python
class RoundRobinAssigner:
    def __init__(self, rotation_window_minutes: int = 5):
        self._rotation_window = timedelta(minutes=rotation_window_minutes)
        self._assignment_history = AssignmentHistory()
        self._current_index = 0
        self._lock = asyncio.Lock()

    async def select_agent(self, available_agents: list[dict]) -> Optional[dict]:
        async with self._lock:
            # Filter out recently assigned agents
            eligible_agents = self._filter_recently_assigned(available_agents)

            if not eligible_agents:
                return None

            # Select next agent in rotation
            selected = eligible_agents[self._current_index % len(eligible_agents)]
            self._current_index += 1

            # Record assignment
            await self._assignment_history.record_assignment(
                agent_id=selected["id"],
                handoff_id=handoff_id
            )

            return selected
```

**Assignment History Management:**
```python
class AssignmentHistory:
    def __init__(self, max_size: int = 1000):
        self._assignments: deque[AssignmentRecord] = deque(maxlen=max_size)
        self._agent_assignments: dict[str, datetime] = {}

    async def record_assignment(self, agent_id: str, handoff_id: str):
        record = AssignmentRecord(
            agent_id=agent_id,
            handoff_id=handoff_id,
            timestamp=datetime.now(timezone.utc)
        )
        self._assignments.append(record)
        self._agent_assignments[agent_id] = record.timestamp

    def was_recently_assigned(self, agent_id: str, window: timedelta) -> bool:
        last_assignment = self._agent_assignments.get(agent_id)
        if not last_assignment:
            return False
        return datetime.now(timezone.utc) - last_assignment < window
```

**Integration with Orchestrator:**
```python
# In HandoffOrchestrator.create_handoff()
available_agents = await self._check_agent_availability_with_fallback(integration)

if available_agents and self._config.round_robin_enabled:
    # Use round-robin assignment
    assigner = self._get_round_robin_assigner(integration.integration_name)
    selected_agent = await assigner.select_agent(available_agents)

    if selected_agent:
        assigned_agent = selected_agent
    else:
        # Fallback to first available if round-robin fails
        assigned_agent = available_agents[0]
        self._logger.warning("Round-robin assignment failed, using fallback")
```

**Performance Requirements:**
- Assignment selection must complete in <100ms
- Use in-memory data structures (no external dependencies)
- Implement efficient circular buffer for history
- Minimize lock contention with async locks

**Configuration Options:**
```python
@dataclass
class RoundRobinConfig:
    enabled: bool = True
    rotation_window_minutes: int = 5
    assignment_history_size: int = 1000
    fallback_retry_attempts: int = 3
    thread_safe: bool = True
```

### Key Technical Considerations

1. **Thread Safety:**
   - Use asyncio.Lock() for async-safe operations
   - Protect shared state (_current_index, assignment history)
   - Support concurrent handoff requests

2. **Memory Management:**
   - Circular buffer for assignment history (fixed max size)
   - Automatic cleanup of old records (>24 hours)
   - Efficient agent lookup with dictionary indexing

3. **Error Handling:**
   - Graceful fallback when round-robin fails
   - Preserve assignment state on errors
   - Comprehensive logging for debugging

4. **Performance Optimization:**
   - In-memory operations only (<100ms requirement)
   - Efficient data structures (deque, dict)
   - Minimal allocations in hot path

5. **State Persistence:**
   - Per-integration round-robin state
   - Reset on integration restart
   - Optional: Persist state across restarts

6. **Monitoring & Observability:**
   - Track assignment distribution metrics
   - Log round-robin decisions
   - Monitor fallback usage

### Implementation Strategy

**Phase 1: Core Round-Robin Implementation**
1. Create RoundRobinAssigner class with basic rotation
2. Implement AssignmentHistory with circular buffer
3. Add thread safety with async locks
4. Write unit tests

**Phase 2: Integration & Configuration**
1. Integrate with HandoffOrchestrator
2. Add configuration options to HandoffConfig
3. Implement fallback mechanisms
4. Write integration tests

**Phase 3: Performance & Polish**
1. Optimize for <100ms performance
2. Add comprehensive error handling
3. Implement monitoring metrics
4. Performance testing

### Testing Approach

**Unit Tests:**
- Test round-robin rotation logic
- Test assignment history management
- Test thread safety with concurrent operations
- Test configuration parameter validation
- Test edge cases (single agent, no agents)

**Integration Tests:**
- Test with HandoffOrchestrator
- Test fallback mechanisms
- Test performance requirements
- Test error scenarios

**Performance Tests:**
- Benchmark assignment selection time
- Test concurrent assignment requests
- Memory usage validation

### Security Considerations

- Validate agent data before assignment
- Prevent circular assignments
- Sanitize logs (no PII in assignment history)
- Rate limiting for assignment requests

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
- Metadata tracking for debugging
- Error handling with graceful fallbacks

**Previous Story Learnings (from 3.8):**
- Instance-level state management (not global)
- Async/await patterns for non-blocking I/O
- Performance optimization with caching
- Comprehensive logging with context
- Fallback mechanisms that don't fail operations

### Project Structure

**Modified Files:**
- `handoffkit/core/orchestrator.py` - Integrate round-robin assignment
- `handoffkit/core/config.py` - Add round-robin configuration
- `handoffkit/integrations/base.py` - Add round-robin support interface

**New Files:**
- `handoffkit/core/round_robin.py` - Round-robin implementation
- `handoffkit/core/assignment_history.py` - Assignment tracking
- `tests/test_round_robin_assignment.py` - Comprehensive test suite

### References

- [Source: handoffkit/core/orchestrator.py] - Current assignment logic
- [Source: handoffkit/core/config.py] - Configuration management
- [Source: handoffkit/core/types.py] - Type definitions
- [Story: 3-8-agent-availability-checking.md] - Previous story implementation

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

**Story 3.9 Created - Ready for Development**

This story implements intelligent agent assignment distribution using a round-robin algorithm to ensure even workload distribution across available agents. Building on the agent availability checking from story 3.8, this adds intelligent selection logic with:

1. **Round-robin rotation** with configurable windows
2. **Assignment history tracking** to prevent immediate reassignment
3. **Thread-safe implementation** for concurrent requests
4. **Performance optimization** (<100ms assignment time)
5. **Comprehensive fallback mechanisms** for reliability

The implementation maintains the established patterns of comprehensive testing, error handling, and metadata tracking while adding intelligent workload distribution capabilities to the handoff system.