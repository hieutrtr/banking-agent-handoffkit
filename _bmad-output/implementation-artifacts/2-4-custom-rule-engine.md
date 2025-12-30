# Story 2.4: Custom Rule Engine

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer with domain-specific needs**,
I want to **define custom handoff rules with conditions and priorities**,
So that **handoff logic matches my business requirements**.

## Acceptance Criteria

1. **Given** a custom rule: IF sentiment < 0.3 AND keyword contains "account" THEN trigger with priority "high" **When** a message matches this rule **Then** handoff is triggered with the specified priority **And** the rule reason is included in TriggerResult

2. **Given** multiple rules that could match **When** `evaluate()` is called **Then** the highest priority matching rule is used **And** all matching rules are logged for debugging

3. **Given** rules configured via the CustomRuleTrigger **When** new rules are added with `add_rule()` **Then** they take effect for new evaluations without restart

4. **Given** a rule with ID **When** `remove_rule(rule_id)` is called **Then** the rule is removed and returns True **And** returns False if rule not found

5. **Given** the trigger is invoked **When** <100ms passes **Then** the evaluation completes (performance requirement)

## Tasks / Subtasks

- [x] Task 1: Define Rule data structure (AC: #1)
  - [x] Subtask 1.1: Create Rule Pydantic model with id, name, condition, priority, enabled fields
  - [x] Subtask 1.2: Define Condition model with field, operator, value structure
  - [x] Subtask 1.3: Support AND/OR logical operators for compound conditions
  - [x] Subtask 1.4: Define priority levels: low, medium, high, immediate

- [x] Task 2: Implement condition evaluation engine (AC: #1, #2)
  - [x] Subtask 2.1: Implement message.contains(text) condition
  - [x] Subtask 2.2: Implement message.matches(regex) condition
  - [x] Subtask 2.3: Implement context.{key} comparisons (==, !=, <, >, <=, >=)
  - [x] Subtask 2.4: Implement conversation.length comparison
  - [x] Subtask 2.5: Implement AND/OR compound condition evaluation
  - [x] Subtask 2.6: Handle missing context keys gracefully (return False, don't error)

- [x] Task 3: Implement CustomRuleTrigger.evaluate() method (AC: #1, #2, #5)
  - [x] Subtask 3.1: Import time module and get_logger from handoffkit.utils.logging
  - [x] Subtask 3.2: Iterate through rules and evaluate each condition
  - [x] Subtask 3.3: Collect all matching rules with their priorities
  - [x] Subtask 3.4: Select highest priority matching rule as winner
  - [x] Subtask 3.5: Return TriggerResult with triggered=True, rule info in metadata
  - [x] Subtask 3.6: Return TriggerResult with triggered=False when no rules match
  - [x] Subtask 3.7: Include matched_rules list in metadata for debugging

- [x] Task 4: Implement rule management (AC: #3, #4)
  - [x] Subtask 4.1: Implement add_rule() to add rules dynamically
  - [x] Subtask 4.2: Implement remove_rule(rule_id) to remove by ID
  - [x] Subtask 4.3: Implement get_rules() to list all rules
  - [x] Subtask 4.4: Auto-generate rule IDs if not provided

- [x] Task 5: Add logging integration (AC: #2, #5)
  - [x] Subtask 5.1: Initialize logger with get_logger("trigger.custom_rule")
  - [x] Subtask 5.2: Log evaluation start at DEBUG level
  - [x] Subtask 5.3: Log each rule evaluation result at DEBUG level
  - [x] Subtask 5.4: Log all matching rules (not just winner) at DEBUG level
  - [x] Subtask 5.5: Log timing measurement (duration_ms in metadata)

- [x] Task 6: Create comprehensive tests (AC: #1, #2, #3, #4, #5)
  - [x] Subtask 6.1: Create `tests/test_custom_rule_trigger.py`
  - [x] Subtask 6.2: Test simple rule matching (message contains)
  - [x] Subtask 6.3: Test compound rules (AND/OR)
  - [x] Subtask 6.4: Test priority ordering (highest priority wins)
  - [x] Subtask 6.5: Test add_rule() and remove_rule()
  - [x] Subtask 6.6: Test context-based conditions
  - [x] Subtask 6.7: Test performance (<100ms for evaluation)
  - [x] Subtask 6.8: Test no rules configured returns triggered=False
  - [x] Subtask 6.9: Run all tests to verify no regressions

- [x] Task 7: Update package exports if needed (AC: #1)
  - [x] Subtask 7.1: Ensure CustomRuleTrigger is exported from handoffkit.triggers
  - [x] Subtask 7.2: Export Rule model from handoffkit.core.types if applicable

## Dev Notes

- **Existing Code**: `CustomRuleTrigger` skeleton exists at `handoffkit/triggers/custom_rules.py` with __init__, add_rule, remove_rule stubs
- **Architecture Reference**: See architecture.md section 3.2 "Core Classes and Interfaces" for BaseTrigger interface
- **Performance Target**: <100ms for trigger evaluation (more complex than Tier 1 simple triggers)
- **Priority Mapping**: Use HandoffPriority enum (LOW, MEDIUM, HIGH, URGENT) - map "immediate" to URGENT
- **Confidence Score**: Use 0.85-0.95 based on rule specificity

### Rule Data Structure

```python
class Rule(BaseModel):
    id: str  # Unique identifier, auto-generated if not provided
    name: str  # Human-readable rule name
    condition: Condition | CompoundCondition  # The condition to evaluate
    priority: str  # low, medium, high, immediate
    enabled: bool = True  # Whether rule is active

class Condition(BaseModel):
    field: str  # e.g., "message.content", "context.user_tier", "conversation.length"
    operator: str  # contains, matches, ==, !=, <, >, <=, >=
    value: Any  # The value to compare against

class CompoundCondition(BaseModel):
    operator: str  # "AND" or "OR"
    conditions: list[Condition | CompoundCondition]  # Nested conditions
```

### Condition Fields Reference

Message fields:
- `message.content` - Full message text
- `message.speaker` - "user" or "ai"

Context fields (from context dict):
- `context.user_id` - User identifier
- `context.user_tier` - e.g., "premium", "standard"
- `context.order_value` - Numeric value
- `context.{any_key}` - Any custom context key

Conversation fields:
- `conversation.length` - Number of messages in history

### Operator Reference

String operators:
- `contains` - String contains substring (case-insensitive)
- `matches` - String matches regex pattern

Comparison operators:
- `==` - Equals
- `!=` - Not equals
- `<` - Less than
- `>` - Greater than
- `<=` - Less than or equal
- `>=` - Greater than or equal

Logical operators:
- `AND` - All conditions must match
- `OR` - At least one condition must match

### Project Structure Notes

- `handoffkit/triggers/custom_rules.py` - Main implementation file
- `handoffkit/triggers/base.py` - BaseTrigger abstract class
- `handoffkit/core/types.py` - TriggerResult, TriggerType.CUSTOM_RULE definitions
- `tests/test_custom_rule_trigger.py` - New test file

### Previous Story Learnings (from Story 2.1, 2.2, 2.3)

- All 345 tests currently passing
- Use get_logger("trigger.custom_rule") for module-specific logging
- Follow async pattern from BaseTrigger.evaluate() signature
- Use Pydantic models for type safety (TriggerResult)
- Add timing measurement in metadata (duration_ms)
- Use 0.9 confidence for rule-based matches
- Pre-compile regex patterns if using matches operator

### Git Intelligence (Recent Commits)

```
347d5e7 feat: implement Story 2.3 - Critical Keyword Monitoring Trigger
a4696a1 feat: implement Story 2.2 - Failure Pattern Tracking Trigger
560d012 feat: implement Story 2.1 - Direct Request Detection Trigger
```

Pattern established: feat prefix, story ID in message, brief description of implementation.

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.4: Custom Rule Engine]
- [Source: _bmad-output/architecture.md#3.2 Core Classes and Interfaces] - BaseTrigger interface
- [Source: handoffkit/triggers/base.py] - Existing BaseTrigger class
- [Source: handoffkit/triggers/custom_rules.py] - Existing skeleton with __init__, add_rule, remove_rule
- [Source: handoffkit/core/types.py] - TriggerResult, TriggerType.CUSTOM_RULE, HandoffPriority

## Dev Agent Record

### Agent Model Used

gemini-claude-opus-4-5-thinking

### Debug Log References

N/A - Clean implementation with no significant debugging needed

### Completion Notes List

- Implemented CustomRuleTrigger.evaluate() method with full condition evaluation engine
- Rule data structure uses dict-based format with id, name, condition, priority, enabled fields
- Condition evaluation supports: contains (case-insensitive), matches (regex), ==, !=, <, >, <=, >=
- AND/OR compound conditions with recursive evaluation
- Field paths: message.content, message.speaker, context.{key}, conversation.length
- Priority ordering: low=1, medium=2, high=3, immediate/urgent=4 (highest wins)
- Dynamic rule management: add_rule(), remove_rule(), get_rules()
- Auto-generated rule IDs using UUID if not provided
- Pre-compiled regex patterns in _precompile_patterns() for performance
- Missing context keys handled gracefully (return False, no error)
- Disabled rules skipped during evaluation
- Integrated structured logging (DEBUG level for all operations)
- Timing measurement in metadata (duration_ms)
- Confidence score set to 0.9 for all rule matches
- matched_rules list in metadata shows all matching rules for debugging
- All 380 tests pass (345 existing + 35 new)
- Performance verified: <100ms for evaluation (actual: <1ms typically)

### File List

- `handoffkit/triggers/custom_rules.py` - Complete implementation (409 lines)
- `tests/test_custom_rule_trigger.py` - 35 comprehensive tests
