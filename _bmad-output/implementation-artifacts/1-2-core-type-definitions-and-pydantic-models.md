# Story 1.2: Core Type Definitions and Pydantic Models

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer integrating HandoffKit**,
I want to **use well-typed data models for messages and configuration**,
so that **I get IDE autocompletion and type safety**.

## Acceptance Criteria

1. **Given** the handoffkit package is imported **When** I create a Message object **Then** I can specify speaker (user/ai), message content, and timestamp **And** Pydantic validates the input types automatically **And** invalid inputs raise clear ValidationError with helpful messages

2. **Given** I need to configure HandoffKit **When** I create a HandoffConfig object **Then** I can set failure_threshold (1-5), sentiment_threshold (0.0-1.0), and critical_keywords (list) **And** default values are sensible (failure=3, sentiment=0.3, keywords=[]) **And** the config is immutable after creation

## Tasks / Subtasks

- [x] Task 1: Enhance Message model with MessageSpeaker enum (AC: #1)
  - [x] Subtask 1.1: Create MessageSpeaker enum in types.py with USER="user" and AI="ai" values
  - [x] Subtask 1.2: Update Message.role field to use MessageSpeaker enum with proper validation
  - [x] Subtask 1.3: Ensure backward compatibility - accept string "user"/"ai"/"assistant" inputs and coerce to enum
  - [x] Subtask 1.4: Add custom validator for helpful error messages on invalid speaker values

- [x] Task 2: Implement validation error customization (AC: #1)
  - [x] Subtask 2.1: Configure Pydantic model_config for custom error messages on Message model
  - [x] Subtask 2.2: Add validation examples in docstrings for IDE hints
  - [x] Subtask 2.3: Test ValidationError messages are user-friendly and actionable

- [x] Task 3: Adjust TriggerConfig validation ranges per specification (AC: #2)
  - [x] Subtask 3.1: Change failure_threshold range from (1-10) to (1-5) per spec
  - [x] Subtask 3.2: Add sentiment_threshold field (0.0-1.0, default 0.3) - currently this is in SentimentConfig as frustration_threshold
  - [x] Subtask 3.3: Verify critical_keywords default is empty list
  - [x] Subtask 3.4: Update test expectations in test_package.py for new failure_threshold max

- [x] Task 4: Make configuration models immutable (AC: #2)
  - [x] Subtask 4.1: Add model_config with frozen=True to HandoffConfig
  - [x] Subtask 4.2: Add model_config with frozen=True to TriggerConfig, SentimentConfig, RoutingConfig, IntegrationConfig
  - [x] Subtask 4.3: Test that attempting to modify config after creation raises appropriate error
  - [x] Subtask 4.4: Add copy-with-changes pattern helper (model_copy with update parameter) for config modifications

- [x] Task 5: Add comprehensive validation tests (AC: #1, #2)
  - [x] Subtask 5.1: Create tests/test_types.py with Message validation tests
  - [x] Subtask 5.2: Create tests/test_config.py with HandoffConfig validation tests
  - [x] Subtask 5.3: Test invalid inputs produce helpful error messages
  - [x] Subtask 5.4: Test immutability behavior
  - [x] Subtask 5.5: Test default values match specification

- [x] Task 6: Update __init__.py exports and verify IDE experience (AC: #1, #2)
  - [x] Subtask 6.1: Export MessageSpeaker enum from handoffkit package
  - [x] Subtask 6.2: Verify all type hints are complete for IDE autocompletion
  - [x] Subtask 6.3: Run mypy type checking on core modules

## Dev Notes

- **Architecture pattern**: Pydantic 2.5+ models with strict validation and frozen config
- **Backward compatibility**: Message model currently uses `role: str` with pattern validation - need to support both enum and string input while storing as enum
- **Immutability**: Use Pydantic's `model_config = ConfigDict(frozen=True)` for all config classes
- **Current state**: types.py already has Message, TriggerResult, SentimentResult, HandoffDecision, HandoffResult; config.py has TriggerConfig, SentimentConfig, RoutingConfig, IntegrationConfig, HandoffConfig
- **Spec discrepancy**: Current TriggerConfig.failure_threshold allows 1-10, spec says 1-5; current SentimentConfig uses frustration_threshold (0.7) and escalation_threshold (0.8), spec mentions sentiment_threshold (0.3)
- **Testing**: pytest with pydantic ValidationError assertions

### Project Structure Notes

- `handoffkit/core/types.py` - Message model, MessageSpeaker enum, result types
- `handoffkit/core/config.py` - All configuration models with immutability
- `handoffkit/__init__.py` - Export MessageSpeaker alongside existing exports
- `tests/test_types.py` - New test file for type validation
- `tests/test_config.py` - New test file for config validation

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 1.2: Core Type Definitions and Pydantic Models]
- [Source: _bmad-output/architecture.md#2.1 Core SDK] - Pydantic 2.5+ requirement
- [Source: handoffkit/core/types.py] - Current Message model implementation
- [Source: handoffkit/core/config.py] - Current config model implementation
- [Source: tests/test_package.py#TestDefaultConfig] - Existing config default tests

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

- All 87 tests pass (0.19s execution time)
- mypy type checking: Success - no issues found in 2 source files

### Completion Notes List

- Created MessageSpeaker enum with USER, AI, and SYSTEM values
- Renamed Message.role field to Message.speaker with MessageSpeaker enum type
- Implemented backward compatibility: strings "user", "ai", "assistant", "system" are coerced to enum (case-insensitive, whitespace-stripped)
- Added comprehensive field_validator with helpful error messages including valid options and examples
- Added sentiment_threshold to TriggerConfig (default 0.3, range 0.0-1.0)
- Changed failure_threshold max from 10 to 5 per specification
- Made all config models immutable with ConfigDict(frozen=True)
- Added comprehensive docstrings with examples for IDE support
- Created 69 new tests across test_types.py and test_config.py
- All 87 tests pass including existing tests

### File List

- handoffkit/core/types.py (modified) - Added MessageSpeaker enum, updated Message model with speaker field and validator
- handoffkit/core/config.py (modified) - Added sentiment_threshold, changed failure_threshold range, added frozen=True to all configs
- handoffkit/__init__.py (modified) - Export MessageSpeaker enum
- tests/conftest.py (modified) - Updated fixtures to use speaker instead of role
- tests/test_package.py (modified) - Updated tests for new Message model and TriggerConfig range
- tests/test_types.py (created) - 31 new tests for type validation
- tests/test_config.py (created) - 38 new tests for config validation
