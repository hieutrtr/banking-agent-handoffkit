# Story 1.3: HandoffOrchestrator Base Interface

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer building a chatbot**,
I want to **instantiate a HandoffOrchestrator with minimal configuration**,
so that **I can start using handoff detection immediately**.

## Acceptance Criteria

1. **Given** the handoffkit package is imported **When** I create `HandoffOrchestrator(helpdesk="zendesk")` **Then** the orchestrator initializes with default triggers and config **And** the orchestrator has `should_handoff()` and `create_handoff()` methods **And** the orchestrator accepts an optional `config` parameter for customization

2. **Given** an orchestrator is created without triggers **When** I call `should_handoff(conversation, message)` **Then** it returns `(False, None)` by default **And** no exceptions are raised

## Tasks / Subtasks

- [x] Task 1: Update HandoffOrchestrator constructor signature (AC: #1)
  - [x] Subtask 1.1: Add `helpdesk` parameter as first positional argument with type `str` (default: "zendesk")
  - [x] Subtask 1.2: Keep `config` as optional keyword argument of type `HandoffConfig`
  - [x] Subtask 1.3: Validate `helpdesk` parameter accepts valid provider values ("zendesk", "intercom", "custom")
  - [x] Subtask 1.4: Store helpdesk in instance variable `_helpdesk`
  - [x] Subtask 1.5: Create default HandoffConfig if none provided

- [x] Task 2: Implement `should_handoff()` method signature (AC: #1, #2)
  - [x] Subtask 2.1: Define synchronous `should_handoff(conversation, current_message)` method
  - [x] Subtask 2.2: Accept `conversation` as `list[Message]` (conversation history)
  - [x] Subtask 2.3: Accept `current_message` as `str` (the message being evaluated)
  - [x] Subtask 2.4: Return type `tuple[bool, Optional[TriggerResult]]`
  - [x] Subtask 2.5: Implement stub that returns `(False, None)` by default

- [x] Task 3: Implement `create_handoff()` method signature (AC: #1)
  - [x] Subtask 3.1: Define synchronous `create_handoff(conversation, metadata)` method
  - [x] Subtask 3.2: Accept `conversation` as `list[Message]` (conversation history)
  - [x] Subtask 3.3: Accept `metadata` as `Optional[dict[str, Any]]` with default `None`
  - [x] Subtask 3.4: Return type `HandoffResult`
  - [x] Subtask 3.5: Implement stub that returns a pending HandoffResult

- [x] Task 4: Add property accessors for configuration (AC: #1)
  - [x] Subtask 4.1: Add `config` property returning `HandoffConfig`
  - [x] Subtask 4.2: Add `helpdesk` property returning `str`
  - [x] Subtask 4.3: Add `triggers` property returning `TriggerConfig` (shortcut to `config.triggers`)

- [x] Task 5: Update package exports (AC: #1)
  - [x] Subtask 5.1: Ensure `HandoffOrchestrator` is exported from `handoffkit.__init__.py`
  - [x] Subtask 5.2: Verify `TriggerResult` is exported for return type annotation

- [x] Task 6: Create comprehensive tests (AC: #1, #2)
  - [x] Subtask 6.1: Create `tests/test_orchestrator.py` with test class
  - [x] Subtask 6.2: Test constructor with helpdesk parameter only
  - [x] Subtask 6.3: Test constructor with helpdesk and config parameters
  - [x] Subtask 6.4: Test invalid helpdesk value raises appropriate error
  - [x] Subtask 6.5: Test `should_handoff()` returns `(False, None)` by default
  - [x] Subtask 6.6: Test `should_handoff()` with empty conversation list
  - [x] Subtask 6.7: Test `should_handoff()` with populated conversation list
  - [x] Subtask 6.8: Test `create_handoff()` returns HandoffResult
  - [x] Subtask 6.9: Test property accessors return correct values
  - [x] Subtask 6.10: Run all tests to verify no regressions (expect 87+ tests passing)

## Dev Notes

- **Signature Change**: Current orchestrator has async methods (`check_handoff_needed`, `execute_handoff`). Story spec shows sync methods (`should_handoff`, `create_handoff`). Implement sync versions per spec - async support can be added later if needed.
- **Constructor Change**: Current constructor only accepts `config`. Need to add `helpdesk` as first parameter per spec: `HandoffOrchestrator(helpdesk="zendesk")`.
- **Return Type**: `should_handoff()` returns a tuple `(bool, Optional[TriggerResult])` - first element is whether to handoff, second is the trigger result if applicable.
- **Stub Implementation**: This story implements the interface/skeleton. Actual trigger detection logic comes in Epic 2.
- **Backward Compatibility**: Consider keeping the async methods as deprecated for one release cycle, or remove them since they only raise NotImplementedError.
- **Type Safety**: Use proper type hints throughout for IDE autocompletion per project patterns established in Story 1.2.

### Project Structure Notes

- `handoffkit/core/orchestrator.py` - Main file to modify with new signature
- `handoffkit/__init__.py` - Verify exports (already exports HandoffOrchestrator)
- `tests/test_orchestrator.py` - New test file to create
- Follow existing test patterns from `tests/test_types.py` and `tests/test_config.py`

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 1.3: HandoffOrchestrator Base Interface]
- [Source: _bmad-output/architecture.md#2.1 Core SDK] - HandoffOrchestrator as primary interface
- [Source: handoffkit/core/orchestrator.py] - Current stub implementation
- [Source: README.md#Quick Start] - Shows expected API usage pattern
- [Source: tests/test_types.py] - Test patterns to follow
- [Source: _bmad-output/implementation-artifacts/1-2-core-type-definitions-and-pydantic-models.md] - Previous story learnings

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

- All 114 tests pass (0.14s execution time)
- mypy type checking: Success - no issues found in 1 source file

### Completion Notes List

- Added `helpdesk` parameter as first positional argument with default "zendesk"
- Implemented validation for valid helpdesk values: "zendesk", "intercom", "custom"
- Added `config` as optional keyword-only argument via `*` separator
- Implemented `should_handoff(conversation, current_message)` returning `tuple[bool, Optional[TriggerResult]]`
- Stub returns `(False, None)` by default per AC #2
- Implemented `create_handoff(conversation, metadata)` returning `HandoffResult`
- Stub returns pending HandoffResult with error message
- Added `helpdesk`, `config`, and `triggers` property accessors
- Removed old async stub methods (`check_handoff_needed`, `execute_handoff`) - they were never implemented
- Created 27 new tests in test_orchestrator.py covering all acceptance criteria
- All 114 tests pass (87 existing + 27 new)

### File List

- handoffkit/core/orchestrator.py (modified) - Complete rewrite with new constructor signature, sync methods, and properties
- tests/test_orchestrator.py (created) - 27 new tests for orchestrator functionality

