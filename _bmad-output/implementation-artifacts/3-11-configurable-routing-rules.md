# Story 3.11: Configurable Routing Rules

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **system administrator configuring handoff routing**,
I want to **define custom routing rules based on conversation content, user attributes, and business logic**,
So that **handoffs are directed to the most appropriate agents or queues automatically**.

## Acceptance Criteria

1. **Given** routing rules are configured **When** handoff is triggered **Then** evaluate all matching rules **And** apply rule actions (assign to agent/queue, set priority, add tags) **And** process in <100ms

2. **Given** multiple rules match **When** priority conflicts occur **Then** use rule precedence (highest first) **And** stop at first matching rule **And** log rule evaluation

3. **Given** no rules match **When** evaluation completes **Then** fall back to default routing (round-robin/availability) **And** mark as unrouted in metadata

## Tasks / Subtasks

- [ ] Task 1: Design routing rule schema and DSL (AC: #1)
  - [ ] Subtask 1.1: Define rule structure (conditions, actions, metadata)
  - [ ] Subtask 1.2: Create condition operators (contains, regex, equals, etc.)
  - [ ] Subtask 1.3: Define action types (assign, priority, tags, department)
  - [ ] Subtask 1.4: Create rule precedence and conflict resolution
  - [ ] Subtask 1.5: Design rule validation system

- [ ] Task 2: Implement rule engine core (AC: #1, #2)
  - [ ] Subtask 2.1: Create RuleEngine class with evaluate() method
  - [ ] Subtask 2.2: Implement condition evaluator with all operators
  - [ ] Subtask 2.3: Implement action executor for each action type
  - [ ] Subtask 2.4: Add rule matching and precedence logic
  - [ ] Subtask 2.5: Ensure <100ms evaluation performance

- [ ] Task 3: Create routing conditions system (AC: #1)
  - [ ] Subtask 3.1: Message content conditions (keywords, sentiment, length)
  - [ ] Subtask 3.2: User attribute conditions (ID, segment, language)
  - [ ] Subtask 3.3: Context conditions (channel, time, conversation history)
  - [ ] Subtask 3.4: Entity conditions (extracted entities, confidence)
  - [ ] Subtask 3.5: Custom field conditions (metadata, tags)

- [ ] Task 4: Implement routing actions (AC: #1)
  - [ ] Subtask 4.1: Agent assignment actions (specific agent, any agent)
  - [ ] Subtask 4.2: Queue/department assignment actions
  - [ ] Subtask 4.3: Priority modification actions
  - [ ] Subtask 4.4: Tag addition/removal actions
  - [ ] Subtask 4.5: Custom field modification actions

- [ ] Task 5: Add configuration management (AC: #1, #2)
  - [ ] Subtask 5.1: Create RoutingConfig with rule definitions
  - [ ] Subtask 5.2: Support rule loading from YAML/JSON files
  - [ ] Subtask 5.3: Add rule hot-reloading capability
  - [ ] Subtask 5.4: Implement rule validation on load
  - [ ] Subtask 5.5: Add rule management API

- [ ] Task 6: Integrate with orchestrator (AC: #1, #2, #3)
  - [ ] Subtask 6.1: Add rule evaluation to create_handoff() flow
  - [ ] Subtask 6.2: Execute rule actions before agent assignment
  - [ ] Subtask 6.3: Handle routing failures gracefully
  - [ ] Subtask 6.4: Add comprehensive rule evaluation metadata
  - [ ] Subtask 6.5: Support rule evaluation callbacks

- [ ] Task 7: Create rule testing framework (AC: #1, #2)
  - [ ] Subtask 7.1: Build rule simulator/tester
  - [ ] Subtask 7.2: Add dry-run mode for rule testing
  - [ ] Subtask 7.3: Create rule performance profiler
  - [ ] Subtask 7.4: Add rule coverage analysis
  - [ ] Subtask 7.5: Implement rule debugging tools

- [ ] Task 8: Implement advanced rule features (AC: #1, #2)
  - [ ] Subtask 8.1: Add rule chaining and composition
  - [ ] Subtask 8.2: Support time-based conditions (business hours)
  - [ ] Subtask 8.3: Implement rule caching for performance
  - [ ] Subtask 8.4: Add rule statistics and metrics
  - [ ] Subtask 8.5: Support A/B testing for rules

- [ ] Task 9: Create comprehensive tests (AC: #1, #2, #3)
  - [ ] Subtask 9.1: Test all condition operators
  - [ ] Subtask 9.2: Test all action types
  - [ ] Subtask 9.3: Test rule precedence and conflicts
  - [ ] Subtask 9.4: Test performance requirements (<100ms)
  - [ ] Subtask 9.5: Test rule validation and error handling
  - [ ] Subtask 9.6: Test integration with orchestrator
  - [ ] Subtask 9.7: Test fallback behavior
  - [ ] Subtask 9.8: Test rule hot-reloading

- [ ] Task 10: Create documentation and examples (AC: #1, #2, #3)
  - [ ] Subtask 10.1: Document rule syntax and operators
  - [ ] Subtask 10.2: Create common routing examples
  - [ ] Subtask 10.3: Document performance best practices
  - [ ] Subtask 10.4: Create troubleshooting guide
  - [ ] Subtask 10.5: Update API documentation

## Dev Notes

### Implementation Context

**Previous Story Learnings (from 3.10 Fallback Tickets):**
- Established pattern: Create fallback when primary routing fails
- Comprehensive error handling with graceful degradation
- User notifications for transparency
- All operations must be thread-safe for async context
- Performance optimization is critical (<100ms requirement)

**Current State of Routing:**
- Basic round-robin and first-available routing implemented
- No custom business logic for routing decisions
- No support for department/queue-based routing
- No conditional routing based on conversation content

### Technical Architecture

**Rule Structure:**
```yaml
routing_rules:
  - name: "VIP Customers"
    priority: 100
    conditions:
      - type: "user_attribute"
        field: "segment"
        operator: "equals"
        value: "vip"
      - type: "conversation_content"
        field: "sentiment"
        operator: "less_than"
        value: 0.3
    actions:
      - type: "assign_to_agent"
        agent_id: "senior-agent-1"
      - type: "set_priority"
        priority: "urgent"
      - type: "add_tags"
        tags: ["vip", "negative_sentiment"]
```

**Rule Engine Design:**
```python
class RuleEngine:
    def __init__(self, rules: list[RoutingRule]):
        self._rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        self._condition_evaluator = ConditionEvaluator()
        self._action_executor = ActionExecutor()

    async def evaluate(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> Optional[RoutingResult]:
        # Evaluate rules in priority order
        for rule in self._rules:
            if await self._matches_rule(rule, context, decision):
                # Execute rule actions
                result = await self._execute_actions(rule.actions, context, decision)
                logger.info(f"Applied routing rule: {rule.name}")
                return result

        # No matching rules
        return None
```

**Condition Types:**
```python
class ConditionType(str, Enum):
    MESSAGE_CONTENT = "message_content"
    USER_ATTRIBUTE = "user_attribute"
    CONTEXT_FIELD = "context_field"
    ENTITY_MATCH = "entity_match"
    METADATA_FIELD = "metadata_field"
    TIME_BASED = "time_based"
    CUSTOM_FUNCTION = "custom_function"

class Operator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCH = "regex_match"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_RANGE = "in_range"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
```

**Action Types:**
```python
class ActionType(str, Enum):
    ASSIGN_TO_AGENT = "assign_to_agent"
    ASSIGN_TO_QUEUE = "assign_to_queue"
    ASSIGN_TO_DEPARTMENT = "assign_to_department"
    SET_PRIORITY = "set_priority"
    ADD_TAGS = "add_tags"
    REMOVE_TAGS = "remove_tags"
    SET_CUSTOM_FIELD = "set_custom_field"
    ROUTE_TO_FALLBACK = "route_to_fallback"
```

**Condition Evaluation:**
```python
class ConditionEvaluator:
    async def evaluate(
        self,
        condition: Condition,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> bool:
        # Extract value based on condition type
        value = await self._extract_value(condition, context, decision)

        # Apply operator
        return self._apply_operator(
            value,
            condition.operator,
            condition.value
        )

    def _extract_value(self, condition, context, decision) -> Any:
        if condition.type == ConditionType.MESSAGE_CONTENT:
            return self._get_message_content(condition.field, context)
        elif condition.type == ConditionType.USER_ATTRIBUTE:
            return context.metadata.get("user", {}).get(condition.field)
        # ... other types
```

**Performance Optimizations:**
```python
# Rule compilation for faster evaluation
compiled_rules = []
for rule in rules:
    compiled_conditions = []
    for condition in rule.conditions:
        compiled_conditions.append(compile_condition(condition))
    compiled_rules.append((rule, compiled_conditions))

# Async evaluation with early termination
async def evaluate_rule(rule, compiled_conditions, context, decision):
    for condition, compiled in zip(rule.conditions, compiled_conditions):
        if not await compiled.evaluate(context, decision):
            return False  # Short-circuit on first failure
    return True
```

### Key Technical Considerations

1. **Performance Requirements:**
   - Rule evaluation must complete in <100ms
   - Use compiled conditions for faster evaluation
   - Implement rule caching and index structures
   - Batch similar conditions for efficiency

2. **Rule Precedence:**
   - Higher priority rules evaluated first
   - First matching rule wins (short-circuit)
   - Explicit priority values (1-1000)
   - Default priority for rules without explicit value

3. **Condition Flexibility:**
   - Support for nested conditions (AND/OR logic)
   - Regular expression matching for content
   - Time-based conditions (business hours, holidays)
   - Custom function conditions for complex logic

4. **Action Reliability:**
   - Validate actions before execution
   - Rollback on partial failures
   - Graceful degradation if action fails
   - Comprehensive logging of actions

5. **Configuration Management:**
   - YAML/JSON configuration files
   - Hot-reloading without restart
   - Rule validation on load
   - Version control for rule changes

6. **Testing and Debugging:**
   - Rule simulation without execution
   - Performance profiling tools
   - Rule coverage analysis
   - Detailed evaluation logs

### Implementation Strategy

**Phase 1: Core Rule Engine**
1. Design rule schema and DSL
2. Implement condition evaluator
3. Create action executor
4. Build basic rule matching
5. Write unit tests

**Phase 2: Advanced Features**
1. Add all condition types
2. Implement all action types
3. Add rule precedence logic
4. Create configuration system
5. Write integration tests

**Phase 3: Performance & Integration**
1. Optimize for <100ms evaluation
2. Integrate with orchestrator
3. Add caching mechanisms
4. Implement hot-reloading
5. Write performance tests

**Phase 4: Management & Monitoring**
1. Create rule testing framework
2. Add metrics and monitoring
3. Implement rule simulator
4. Create documentation
5. Write end-to-end tests

### Testing Approach

**Unit Tests:**
- Condition evaluation logic
- Action execution
- Rule matching and precedence
- Configuration validation
- Performance benchmarks

**Integration Tests:**
- Full routing flow with orchestrator
- Rule hot-reloading
- Fallback behavior
- Error handling
- Concurrent rule evaluation

**Performance Tests:**
- Evaluation time under 100ms
- Memory usage with many rules
- Concurrent evaluation performance
- Rule compilation efficiency

### Security Considerations

- Validate all rule inputs
- Sanitize regex patterns
- Limit rule execution time
- Prevent infinite loops
- Secure configuration files
- Audit rule changes

### Git Intelligence (Recent Commits)

```
5dbe139 feat(3-9): implement round-robin agent distribution with fallback
24bdb8a feat(3-8): implement agent availability checking with caching and assignment
0978e61 chore(3-6): mark story as done
e9c5542 feat(3-6): implement Intercom integration adapter with code review fixes
53193c6 fix(3-4): code review - fix template format and test coverage
```

**Established Patterns:**
- Commit format: `feat(X-Y): implement <description>`
- Comprehensive test coverage required
- All tests must pass before marking done
- Thread-safe async implementation
- Performance requirements (<100ms)
- Graceful error handling and logging

**Previous Story Learnings (from 3.10):**
- Fallback mechanisms ensure reliability
- User notifications maintain transparency
- Local storage provides resilience
- Async/await for non-blocking operations
- Configuration-driven behavior

### Project Structure

**New Files:**
- `handoffkit/routing/rules.py` - Rule definitions and models
- `handoffkit/routing/engine.py` - Rule evaluation engine
- `handoffkit/routing/conditions.py` - Condition implementations
- `handoffkit/routing/actions.py` - Action implementations
- `handoffkit/routing/config.py` - Routing configuration
- `handoffkit/routing/__init__.py` - Package exports
- `tests/test_routing_rules.py` - Comprehensive test suite

**Modified Files:**
- `handoffkit/core/orchestrator.py` - Add rule evaluation
- `handoffkit/core/config.py` - Add routing rule configuration
- `handoffkit/integrations/base.py` - Add routing support interface

### References

- [Source: handoffkit/core/orchestrator.py] - Current routing logic
- [Source: handoffkit/core/config.py] - Configuration management
- [Source: handoffkit/integrations/base.py] - Base integration patterns
- [Story: 3-10-fallback-ticket-creation.md] - Previous story implementation
- [Business Rules Engine Pattern] - https://martinfowler.com/bliki/BusinessRulesEngine.html

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

**Story 3.11 Created - Ready for Development**

This story implements a sophisticated configurable routing rule system that allows administrators to define custom business logic for directing handoffs. Building on the round-robin distribution and fallback mechanisms from previous stories, this adds intelligent routing based on:

1. **Conversation Content Analysis** - Keywords, sentiment, entities
2. **User Attributes** - Segment, language, history
3. **Context Information** - Channel, time, metadata
4. **Custom Business Logic** - Department rules, SLA requirements

The implementation provides:
- Declarative rule syntax in YAML/JSON
- High-performance rule evaluation (<100ms)
- Comprehensive condition and action types
- Hot-reloading for rule updates
- Rule testing and simulation tools
- Full integration with the orchestrator

This completes the intelligent routing capabilities of HandoffKit, enabling sophisticated handoff management tailored to specific business needs.