# Story 2.3: Critical Keyword Monitoring Trigger

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **chatbot developer handling sensitive topics**,
I want to **immediately escalate conversations mentioning fraud, emergencies, or security issues**,
So that **urgent matters get human attention instantly**.

## Acceptance Criteria

1. **Given** a message containing "fraud" or "unauthorized transaction" **When** `evaluate()` is called **Then** it triggers immediately with trigger_type=KEYWORD **And** priority is set to "immediate"

2. **Given** default critical keywords: ["fraud", "emergency", "locked out", "dispute", "unauthorized", "stolen"] **When** any of these appear in a message (case-insensitive) **Then** handoff is triggered

3. **Given** custom keywords configured: ["regulation E", "FDIC complaint"] **When** these phrases appear in a message **Then** handoff is triggered for custom keywords too

4. **Given** the trigger is invoked **When** <50ms passes **Then** the evaluation completes (performance requirement)

5. **Given** case_sensitive=False (default) **When** "FRAUD" or "Fraud" appears in message **Then** it still triggers

## Tasks / Subtasks

- [x] Task 1: Implement KeywordTrigger.evaluate() method (AC: #1, #2, #5)
  - [x] Subtask 1.1: Import time module and get_logger from handoffkit.utils.logging
  - [x] Subtask 1.2: Pre-compile keyword patterns in __init__ using regex word boundaries
  - [x] Subtask 1.3: Implement evaluate() to check message content against all patterns
  - [x] Subtask 1.4: Return TriggerResult with triggered=True, trigger_type=CRITICAL_KEYWORD on match
  - [x] Subtask 1.5: Return TriggerResult with triggered=False when no keyword matches
  - [x] Subtask 1.6: Include matched_keyword in metadata for debugging

- [x] Task 2: Define keyword categories (AC: #1, #2)
  - [x] Subtask 2.1: Financial keywords: fraud, unauthorized, stolen, dispute, chargeback
  - [x] Subtask 2.2: Safety keywords: emergency, threat, danger, harm, suicide, crisis
  - [x] Subtask 2.3: Legal keywords: lawsuit, attorney, lawyer, legal action, sue
  - [x] Subtask 2.4: Urgency keywords: urgent, immediately, asap, right now, critical
  - [x] Subtask 2.5: Access keywords: locked out, locked account, cannot access

- [x] Task 3: Implement custom keywords support (AC: #3)
  - [x] Subtask 3.1: Accept custom keywords list in __init__
  - [x] Subtask 3.2: Merge custom keywords with defaults or replace entirely
  - [x] Subtask 3.3: Support multi-word phrases (e.g., "regulation E", "FDIC complaint")

- [x] Task 4: Add case sensitivity option (AC: #5)
  - [x] Subtask 4.1: Use re.IGNORECASE flag when case_sensitive=False
  - [x] Subtask 4.2: Use literal regex when case_sensitive=True

- [x] Task 5: Add logging integration (AC: #4)
  - [x] Subtask 5.1: Initialize logger with get_logger("trigger.keyword")
  - [x] Subtask 5.2: Log evaluation start at DEBUG level
  - [x] Subtask 5.3: Log matched keyword or no-match at DEBUG level
  - [x] Subtask 5.4: Log timing measurement (duration_ms in metadata)

- [x] Task 6: Create comprehensive tests (AC: #1, #2, #3, #4, #5)
  - [x] Subtask 6.1: Create `tests/test_keyword_trigger.py`
  - [x] Subtask 6.2: Test default keywords trigger (fraud, emergency, etc.)
  - [x] Subtask 6.3: Test case insensitivity (FRAUD, Fraud, fraud)
  - [x] Subtask 6.4: Test custom keywords
  - [x] Subtask 6.5: Test multi-word phrases
  - [x] Subtask 6.6: Test performance (<50ms for evaluation)
  - [x] Subtask 6.7: Test trigger_type is CRITICAL_KEYWORD
  - [x] Subtask 6.8: Test no false positives on normal messages
  - [x] Subtask 6.9: Run all tests to verify no regressions (345 tests passing)

- [x] Task 7: Update package exports if needed (AC: #1)
  - [x] Subtask 7.1: Ensure KeywordTrigger is exported from handoffkit.triggers
  - [x] Subtask 7.2: Verify integration with factory pattern

## Dev Notes

- **Existing Code**: `KeywordTrigger` skeleton exists at `handoffkit/triggers/keyword.py` with __init__ already accepting keywords and case_sensitive
- **Architecture Reference**: See architecture.md section 3.2 "Core Classes and Interfaces" for BaseTrigger interface
- **Performance Target**: <50ms for trigger evaluation (Tier 1 rule-based should be <10ms)
- **Pattern Matching**: Use pre-compiled regex patterns with word boundaries for accurate matching
- **Confidence Score**: Use 0.95 for keyword matches (high certainty)
- **Priority**: Keywords should indicate "immediate" priority in metadata

### Keyword Categories (from architecture.md and PRD)

Financial:
- "fraud"
- "unauthorized"
- "stolen"
- "dispute"
- "chargeback"

Safety:
- "emergency"
- "threat"
- "danger"
- "harm"
- "suicide"
- "crisis"

Legal:
- "lawsuit"
- "attorney"
- "lawyer"
- "legal action"
- "sue"

Urgency:
- "urgent"
- "immediately"
- "asap"
- "right now"
- "critical"

Access:
- "locked out"
- "locked account"
- "cannot access"

### Pattern Matching Strategy

Use word boundary matching to avoid false positives:
1. For single words: `r"\bfraud\b"` matches "fraud" but not "defraud"
2. For multi-word phrases: `r"\blocked\s+out\b"` matches "locked out"
3. Pre-compile all patterns in __init__ for performance

### Project Structure Notes

- `handoffkit/triggers/keyword.py` - Main implementation file
- `handoffkit/triggers/base.py` - BaseTrigger abstract class
- `handoffkit/core/types.py` - TriggerResult, TriggerType.CRITICAL_KEYWORD definitions
- `tests/test_keyword_trigger.py` - New test file

### Previous Story Learnings (from Story 2.1, 2.2)

- All 287 tests currently passing
- Use get_logger("trigger.keyword") for module-specific logging
- Follow async pattern from BaseTrigger.evaluate() signature
- Use Pydantic models for type safety (TriggerResult)
- Pre-compile regex patterns in __init__ for performance
- Use early exit on first match (no need to check all)
- Add timing measurement in metadata (duration_ms)
- Use 0.95 confidence for high-confidence keyword matches

### Git Intelligence (Recent Commits)

```
a4696a1 feat: implement Story 2.2 - Failure Pattern Tracking Trigger
560d012 feat: implement Story 2.1 - Direct Request Detection Trigger
e2fcea2 feat: implement Story 1.5 - Structured Logging Utilities
```

Pattern established: feat prefix, story ID in message, brief description of implementation.

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.3: Critical Keyword Monitoring Trigger]
- [Source: _bmad-output/architecture.md#3.2 Core Classes and Interfaces] - BaseTrigger interface
- [Source: _bmad-output/architecture.md#2.6 LLM Integration Architecture] - Tier 1 rule-based detection
- [Source: handoffkit/triggers/base.py] - Existing BaseTrigger class
- [Source: handoffkit/triggers/keyword.py] - Existing skeleton with __init__
- [Source: handoffkit/triggers/direct_request.py] - Reference implementation pattern
- [Source: handoffkit/core/types.py] - TriggerResult, TriggerType.CRITICAL_KEYWORD

## Dev Agent Record

### Agent Model Used

gemini-claude-opus-4-5-thinking

### Debug Log References

N/A - Clean implementation with no significant debugging needed

### Completion Notes List

- Implemented KeywordTrigger.evaluate() method with full pattern matching
- Added 24 default keywords across 5 categories (Financial, Safety, Legal, Urgency, Access)
- Pre-compiled regex patterns with word boundaries in __init__ for performance
- Implemented case sensitivity option (case_sensitive=False by default)
- Custom keywords fully replace defaults when provided
- Multi-word phrases supported with flexible whitespace matching (`\s+`)
- Integrated structured logging (DEBUG level for all operations)
- Added timing measurement in metadata (duration_ms)
- Confidence score set to 0.95 for all keyword matches
- Priority set to "immediate" in metadata for triggered results
- Word boundary matching prevents false positives (e.g., "defraud" doesn't match "fraud")
- All 345 tests pass (287 existing + 58 new)
- Performance verified: <50ms for evaluation (actual: <1ms typically)

### File List

- `handoffkit/triggers/keyword.py` - Complete implementation (161 lines)
- `tests/test_keyword_trigger.py` - 58 comprehensive tests
