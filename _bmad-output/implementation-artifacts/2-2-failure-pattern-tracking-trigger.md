# Story 2.2: Failure Pattern Tracking Trigger

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **chatbot developer**,
I want to **detect when the AI has failed to help multiple times**,
so that **frustrated users get human assistance**.

## Acceptance Criteria

1. **Given** a conversation where the user repeats the same question 3 times **When** `evaluate()` is called **Then** it returns triggered=True with trigger_type=FAILURE_PATTERN

2. **Given** the AI responds with "I don't understand" 2 times **When** `evaluate()` is called with failure_threshold=2 **Then** it triggers on the 2nd failure

3. **Given** a single failed response followed by successful help **When** `evaluate()` is called **Then** it returns triggered=False (counter was reset)

4. **Given** the trigger is invoked **When** <100ms passes **Then** the evaluation completes (performance requirement)

5. **Given** configurable threshold (1-5) **When** threshold is set **Then** trigger respects the configured value

## Tasks / Subtasks

- [x] Task 1: Implement FailureTrackingTrigger.evaluate() method (AC: #1, #2, #3, #5)
  - [x] Subtask 1.1: Import time module and get_logger from handoffkit.utils.logging
  - [x] Subtask 1.2: Add failure detection patterns in __init__ (pre-compiled regex)
  - [x] Subtask 1.3: Implement _count_failures() to count AI failure patterns in history
  - [x] Subtask 1.4: Implement _detect_repeated_questions() to find user repetition
  - [x] Subtask 1.5: Implement _detect_success() to check for successful exchanges
  - [x] Subtask 1.6: Return TriggerResult with triggered=True when failures >= threshold
  - [x] Subtask 1.7: Return TriggerResult with triggered=False when failures < threshold

- [x] Task 2: Define failure detection patterns (AC: #1, #2)
  - [x] Subtask 2.1: Add AI failure phrases: "I don't understand", "I'm not sure", "I cannot help with that"
  - [x] Subtask 2.2: Add user frustration indicators: "you're not helping", "that's not what I asked", "I already said"
  - [x] Subtask 2.3: Add repetition detection using similarity scoring (simple word overlap)
  - [x] Subtask 2.4: Add bot loop detection (same AI response repeated)

- [x] Task 3: Implement success reset logic (AC: #3)
  - [x] Subtask 3.1: Define success indicators: "thanks", "that helps", "perfect", "got it"
  - [x] Subtask 3.2: Implement logic to reset failure counter on success detection
  - [x] Subtask 3.3: Track consecutive failures only (not total)

- [x] Task 4: Add logging integration (AC: #4)
  - [x] Subtask 4.1: Initialize logger with get_logger("trigger.failure_tracking")
  - [x] Subtask 4.2: Log evaluation start at DEBUG level
  - [x] Subtask 4.3: Log failure count and threshold at DEBUG level
  - [x] Subtask 4.4: Log timing measurement (duration_ms in metadata)

- [x] Task 5: Create comprehensive tests (AC: #1, #2, #3, #4, #5)
  - [x] Subtask 5.1: Create `tests/test_failure_tracking_trigger.py`
  - [x] Subtask 5.2: Test repeated questions trigger (3 times)
  - [x] Subtask 5.3: Test AI "I don't understand" triggers with threshold=2
  - [x] Subtask 5.4: Test success resets failure counter
  - [x] Subtask 5.5: Test configurable threshold (1, 2, 3, 4, 5)
  - [x] Subtask 5.6: Test performance (<100ms for evaluation)
  - [x] Subtask 5.7: Test trigger_type is FAILURE_PATTERN
  - [x] Subtask 5.8: Run all tests to verify no regressions (287 tests passing)

- [x] Task 6: Update package exports if needed (AC: #1)
  - [x] Subtask 6.1: Ensure FailureTrackingTrigger is exported from handoffkit.triggers
  - [x] Subtask 6.2: Verify integration with factory pattern

## Dev Notes

- **Existing Code**: `FailureTrackingTrigger` skeleton exists at `handoffkit/triggers/failure_tracking.py` with __init__ already accepting failure_threshold and failure_window
- **Architecture Reference**: See architecture.md section 3.2 "Core Classes and Interfaces" for BaseTrigger interface
- **Performance Target**: <100ms for trigger evaluation (Tier 1 rule-based should be <10ms)
- **Pattern Matching**: Use pre-compiled regex patterns for performance (follow Story 2.1 pattern)
- **Confidence Score**: Use 0.85-0.95 based on failure severity
- **History Required**: This trigger REQUIRES conversation history to function

### Failure Patterns to Detect (from architecture.md)

AI failure indicators:
- "I don't understand"
- "I'm not sure what you mean"
- "I cannot help with that"
- "Could you please rephrase"
- "I'm having trouble understanding"

User frustration indicators:
- "You're not helping"
- "That's not what I asked"
- "I already told you"
- "You keep saying the same thing"
- "This doesn't work"

Success indicators (reset counter):
- "Thanks" / "Thank you"
- "That helps" / "That worked"
- "Perfect" / "Great"
- "Got it" / "Understood"
- "Awesome" / "Exactly"

### Similarity Detection

For repeated question detection, use simple word overlap:
1. Tokenize messages (split by whitespace, lowercase)
2. Calculate Jaccard similarity: |intersection| / |union|
3. If similarity > 0.6 between current and previous user messages → count as repetition

### Project Structure Notes

- `handoffkit/triggers/failure_tracking.py` - Main implementation file
- `handoffkit/triggers/base.py` - BaseTrigger abstract class
- `handoffkit/core/types.py` - TriggerResult, TriggerType definitions
- `tests/test_failure_tracking_trigger.py` - New test file

### Previous Story Learnings (from Story 2.1)

- All 246 tests currently passing
- Use get_logger("trigger.failure_tracking") for module-specific logging
- Follow async pattern from BaseTrigger.evaluate() signature
- Use Pydantic models for type safety (TriggerResult)
- Pre-compile regex patterns in __init__ for performance
- Use early exit on first match (no need to check all)
- Add timing measurement in metadata (duration_ms)
- Use 0.9 confidence for high-confidence matches

### Git Intelligence (Recent Commits)

```
560d012 feat: implement Story 2.1 - Direct Request Detection Trigger
e2fcea2 feat: implement Story 1.5 - Structured Logging Utilities
33af8bf feat: implement Story 1.4 - Configuration Management System
```

Pattern established: feat prefix, story ID in message, brief description of implementation.

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.2: Failure Pattern Tracking Trigger]
- [Source: _bmad-output/architecture.md#3.2 Core Classes and Interfaces] - BaseTrigger interface
- [Source: _bmad-output/architecture.md#2.6 LLM Integration Architecture] - Tier 1 rule-based detection
- [Source: handoffkit/triggers/base.py] - Existing BaseTrigger class
- [Source: handoffkit/triggers/failure_tracking.py] - Existing skeleton with __init__
- [Source: handoffkit/triggers/direct_request.py] - Reference implementation pattern
- [Source: handoffkit/core/types.py] - TriggerResult, TriggerType.FAILURE_PATTERN

## Dev Agent Record

### Agent Model Used

gemini-claude-opus-4-5-thinking

### Debug Log References

N/A - Clean implementation with no significant debugging needed

### Completion Notes List

- Implemented FailureTrackingTrigger.evaluate() method with full pattern matching
- Added 8 AI failure patterns (I don't understand, I'm not sure, etc.)
- Added 8 user frustration patterns (you're not helping, that's not what I asked, etc.)
- Added 11 success indicator patterns to reset failure counter (thanks, perfect, got it, etc.)
- Implemented Jaccard similarity calculation for repeated question detection (threshold: 0.5)
- Implemented bot loop detection (same AI response repeated with similarity > 0.8)
- Pre-compiled all patterns in __init__ for performance
- Integrated structured logging (DEBUG level for all operations)
- Added timing measurement in metadata (duration_ms)
- Confidence score scales from 0.8 to 0.9 based on failure count over threshold
- All 287 tests pass (41 new + 246 existing)
- Performance verified: <100ms for evaluation (actual: <1ms typically)

### File List

- `handoffkit/triggers/failure_tracking.py` - Complete implementation
- `tests/test_failure_tracking_trigger.py` - 41 comprehensive tests

