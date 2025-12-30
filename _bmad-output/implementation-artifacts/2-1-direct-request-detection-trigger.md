# Story 2.1: Direct Request Detection Trigger

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer integrating HandoffKit**,
I want to **detect when users explicitly request human assistance**,
so that **I can immediately route them to a human agent**.

## Acceptance Criteria

1. **Given** a user says "I want to talk to a human" **When** the message is evaluated **Then** the trigger returns true with >0.8 confidence

2. **Given** a user asks a normal question **When** the message is evaluated **Then** the trigger returns false

3. **Given** various phrasings **When** messages are processed **Then** all common variations are detected ("agent", "representative", "real person", etc.)

4. **Given** the trigger is invoked **When** <100ms passes **Then** the evaluation completes (performance requirement)

## Tasks / Subtasks

- [x] Task 1: Implement DirectRequestTrigger.evaluate() method (AC: #1, #2, #3)
  - [x] Subtask 1.1: Import re module and compile default patterns in __init__
  - [x] Subtask 1.2: Implement evaluate() to match patterns against message.content
  - [x] Subtask 1.3: Return TriggerResult with triggered=True, trigger_type=DIRECT_REQUEST, confidence>0.8 on match
  - [x] Subtask 1.4: Return TriggerResult with triggered=False, confidence=0.0 when no match
  - [x] Subtask 1.5: Include matched pattern in reason field for debugging

- [x] Task 2: Expand pattern coverage for common variations (AC: #3)
  - [x] Subtask 2.1: Add patterns for "agent", "representative", "operator", "support"
  - [x] Subtask 2.2: Add patterns for "escalate", "supervisor", "manager"
  - [x] Subtask 2.3: Add patterns for frustrated requests ("just get me", "please transfer", "I demand")
  - [x] Subtask 2.4: Add negative patterns to avoid false positives ("not a human", "don't need agent")

- [x] Task 3: Implement performance optimizations (AC: #4)
  - [x] Subtask 3.1: Pre-compile regex patterns in __init__ (not on each evaluate call)
  - [x] Subtask 3.2: Use early exit on first pattern match (no need to check all)
  - [x] Subtask 3.3: Add timing measurement for performance validation

- [x] Task 4: Add logging integration (AC: #1, #2, #3, #4)
  - [x] Subtask 4.1: Import get_logger from handoffkit.utils.logging
  - [x] Subtask 4.2: Log trigger evaluation at DEBUG level with message preview
  - [x] Subtask 4.3: Log trigger result at DEBUG level with triggered, confidence, reason
  - [x] Subtask 4.4: Log timing at DEBUG level for performance monitoring

- [x] Task 5: Create comprehensive tests (AC: #1, #2, #3, #4)
  - [x] Subtask 5.1: Create `tests/test_direct_request_trigger.py`
  - [x] Subtask 5.2: Test explicit requests return triggered=True with confidence>0.8
  - [x] Subtask 5.3: Test normal questions return triggered=False
  - [x] Subtask 5.4: Test all pattern variations (agent, representative, person, etc.)
  - [x] Subtask 5.5: Test case insensitivity
  - [x] Subtask 5.6: Test negative patterns don't false positive
  - [x] Subtask 5.7: Test performance (<100ms for evaluation)
  - [x] Subtask 5.8: Run all tests to verify no regressions (246 tests passing)

- [x] Task 6: Update package exports if needed (AC: #1)
  - [x] Subtask 6.1: Ensure DirectRequestTrigger is exported from handoffkit.triggers
  - [x] Subtask 6.2: Verify integration with HandoffOrchestrator

## Dev Notes

- **Existing Code**: `DirectRequestTrigger` skeleton exists at `handoffkit/triggers/direct_request.py` with default patterns already defined
- **Architecture Reference**: See architecture.md section 3.2 "Core Classes and Interfaces" for BaseTrigger interface
- **Performance Target**: <100ms for trigger evaluation (Tier 1 rule-based should be <10ms)
- **Pattern Matching**: Use compiled regex patterns for performance
- **Confidence Score**: Use 0.9 for exact matches, 0.8 for fuzzy matches
- **Thread Safety**: ensure patterns are compiled once and reused

### Patterns to Detect (from architecture.md)

Common phrases to detect:
- "Talk to a human" / "speak to a human"
- "I need a real person"
- "Connect me to an agent"
- "Let me speak to someone"
- "Transfer me to support"
- "Get me a representative"
- "I want to talk to your manager"
- "Escalate this issue"

### Project Structure Notes

- `handoffkit/triggers/direct_request.py` - Main implementation file
- `handoffkit/triggers/base.py` - BaseTrigger abstract class
- `handoffkit/core/types.py` - TriggerResult, TriggerType definitions
- `tests/test_direct_request_trigger.py` - New test file

### Previous Story Learnings (from Epic 1)

- All 209 tests currently passing
- Use get_logger("trigger.direct_request") for module-specific logging
- Follow async pattern from BaseTrigger.evaluate() signature
- Use Pydantic models for type safety (TriggerResult)

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.1: Direct Request Detection Trigger]
- [Source: _bmad-output/architecture.md#3.2 Core Classes and Interfaces] - BaseTrigger interface
- [Source: _bmad-output/architecture.md#2.6 LLM Integration Architecture] - Tier 1 rule-based detection
- [Source: handoffkit/triggers/base.py] - Existing BaseTrigger class
- [Source: handoffkit/triggers/direct_request.py] - Existing skeleton with patterns
- [Source: handoffkit/core/types.py] - TriggerResult, TriggerType definitions

## Dev Agent Record

### Agent Model Used

gemini-claude-opus-4-5-thinking

### Debug Log References

N/A - Clean implementation with no significant debugging needed

### Completion Notes List

- Implemented DirectRequestTrigger.evaluate() method with full pattern matching
- Added 13 comprehensive regex patterns covering common variations:
  - talk/speak/connect patterns with a/an handling
  - need/want patterns for real/human/live person
  - transfer patterns including "please transfer me"
  - get me patterns for human/agent/operator
  - escalation patterns for supervisor/manager
  - demand patterns for frustrated users
- Added 2 negative patterns to avoid false positives (don't need, not asking)
- Pre-compiled all patterns in __init__ for performance
- Early exit on first match for optimal performance
- Added timing measurement in metadata (duration_ms)
- Integrated structured logging (DEBUG level for all operations)
- All 246 tests pass (37 new + 209 existing)
- Performance verified: <100ms for evaluation (actual: <1ms typically)

### File List

- `handoffkit/triggers/direct_request.py` - Complete implementation
- `tests/test_direct_request_trigger.py` - 37 comprehensive tests

