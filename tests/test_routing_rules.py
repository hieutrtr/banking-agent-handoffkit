"""Tests for routing rules functionality."""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List

from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    Message,
    Speaker,
    TriggerResult,
)
from handoffkit.routing import (
    RoutingEngine,
    RoutingRule,
    RoutingResult,
    RoutingConfig,
    Condition,
    RuleAction,
    RuleActionType,
    ConditionType,
    Operator,
)


class TestRoutingRules:
    """Test routing rules functionality."""

    @pytest.fixture
    def sample_context(self) -> ConversationContext:
        """Create sample conversation context."""
        return ConversationContext(
            conversation_id="test-conv-123",
            user_id="user-456",
            messages=[
                Message(
                    content="I need help with my billing issue",
                    speaker=Speaker.USER,
                    timestamp=datetime.now(timezone.utc),
                ),
                Message(
                    content="I'll help you with your billing issue",
                    speaker=Speaker.AI,
                    timestamp=datetime.now(timezone.utc),
                ),
            ],
            metadata={
                "channel": "web",
                "extracted_entities": [
                    {"entity_type": "issue_type", "value": "billing"}
                ],
            },
        )

    @pytest.fixture
    def sample_decision(self) -> HandoffDecision:
        """Create sample handoff decision."""
        return HandoffDecision(
            should_handoff=True,
            confidence=0.9,
            reason="Customer has billing issue",
            priority=HandoffPriority.MEDIUM,
            trigger_results=[
                TriggerResult(
                    trigger_type="keyword_match",
                    confidence=0.9,
                    reason="billing keyword detected",
                    metadata={"keyword": "billing"},
                )
            ],
        )

    @pytest.fixture
    def sample_metadata(self) -> Dict[str, Any]:
        """Create sample metadata."""
        return {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "tier": "premium",
            },
            "channel": "web",
        }

    def test_rule_action_validation(self):
        """Test rule action validation."""
        # Valid action
        action = RuleAction(
            type=RuleActionType.ASSIGN_TO_AGENT,
            parameters={"agent_id": "agent-123"}
        )
        assert action.type == "assign_to_agent"
        assert action.get_agent_id() == "agent-123"

        # Invalid action type
        with pytest.raises(ValueError, match="Invalid action type"):
            RuleAction(type="invalid_type", parameters={})

    def test_condition_validation(self):
        """Test condition validation."""
        # Valid condition
        condition = Condition(
            type=ConditionType.MESSAGE_CONTENT,
            field="content",
            operator=Operator.CONTAINS,
            value="billing"
        )
        assert condition.type.value == "message_content"
        assert condition.field == "content"

        # Missing field for message_content
        with pytest.raises(ValueError, match="field is required"):
            Condition(
                type=ConditionType.MESSAGE_CONTENT,
                operator=Operator.CONTAINS,
                value="billing"
            )

    def test_routing_rule_creation(self):
        """Test routing rule creation."""
        rule = RoutingRule(
            name="billing_issue_rule",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.CONTAINS,
                    "value": "billing"
                }
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ASSIGN_TO_QUEUE,
                    parameters={"queue_name": "billing_queue"}
                )
            ]
        )

        assert rule.name == "billing_issue_rule"
        assert rule.priority == 100
        assert len(rule.conditions) == 1
        assert len(rule.actions) == 1

    @pytest.mark.asyncio
    async def test_condition_evaluation_message_content(self, sample_context, sample_decision, sample_metadata):
        """Test message content condition evaluation."""
        condition = Condition(
            type=ConditionType.MESSAGE_CONTENT,
            field="content",
            operator=Operator.CONTAINS,
            value="billing"
        )

        result = await condition.evaluate(sample_context, sample_decision, sample_metadata)
        assert result is True

        # Test negative case
        condition.value = "shipping"
        result = await condition.evaluate(sample_context, sample_decision, sample_metadata)
        assert result is False

    @pytest.mark.asyncio
    async def test_condition_evaluation_user_attribute(self, sample_context, sample_decision, sample_metadata):
        """Test user attribute condition evaluation."""
        condition = Condition(
            type=ConditionType.USER_ATTRIBUTE,
            field="tier",
            operator=Operator.EQUALS,
            value="premium"
        )

        result = await condition.evaluate(sample_context, sample_decision, sample_metadata)
        assert result is True

        # Test non-premium user
        condition.value = "basic"
        result = await condition.evaluate(sample_context, sample_decision, sample_metadata)
        assert result is False

    @pytest.mark.asyncio
    async def test_condition_evaluation_context_field(self, sample_context, sample_decision, sample_metadata):
        """Test context field condition evaluation."""
        condition = Condition(
            type=ConditionType.CONTEXT_FIELD,
            field="channel",
            operator=Operator.EQUALS,
            value="web"
        )

        result = await condition.evaluate(sample_context, sample_decision, sample_metadata)
        assert result is True

    @pytest.mark.asyncio
    async def test_condition_evaluation_entity(self, sample_context, sample_decision, sample_metadata):
        """Test entity condition evaluation."""
        condition = Condition(
            type=ConditionType.ENTITY,
            field="issue_type",
            operator=Operator.EQUALS,
            value="billing"
        )

        result = await condition.evaluate(sample_context, sample_decision, sample_metadata)
        assert result is True

    @pytest.mark.asyncio
    async def test_condition_evaluation_trigger(self, sample_context, sample_decision, sample_metadata):
        """Test trigger condition evaluation."""
        condition = Condition(
            type=ConditionType.TRIGGER,
            field="trigger_type",
            operator=Operator.EQUALS,
            value="keyword_match"
        )

        result = await condition.evaluate(sample_context, sample_decision, sample_metadata)
        assert result is True

    @pytest.mark.asyncio
    async def test_routing_engine_basic_rule(self, sample_context, sample_decision, sample_metadata):
        """Test basic rule evaluation with routing engine."""
        # Create a simple rule
        rule = RoutingRule(
            name="billing_priority_rule",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.CONTAINS,
                    "value": "billing"
                }
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.SET_PRIORITY,
                    parameters={"priority": "HIGH"}
                ),
                RuleAction(
                    type=RuleActionType.ASSIGN_TO_QUEUE,
                    parameters={"queue_name": "billing_queue"}
                )
            ]
        )

        # Create routing config with the rule
        config = RoutingConfig(
            rules=[rule],
            enable_caching=False  # Disable caching for tests
        )

        # Create routing engine
        engine = RoutingEngine(config)

        # Evaluate rules
        result = await engine.evaluate(sample_context, sample_decision, sample_metadata)

        assert result is not None
        assert result.rule_name == "billing_priority_rule"
        assert len(result.actions_applied) == 2
        assert result.get_priority() == HandoffPriority.HIGH
        assert result.get_assigned_queue() == "billing_queue"

    @pytest.mark.asyncio
    async def test_routing_engine_no_matching_rule(self, sample_context, sample_decision, sample_metadata):
        """Test routing engine when no rules match."""
        # Create a rule that won't match
        rule = RoutingRule(
            name="shipping_rule",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.CONTAINS,
                    "value": "shipping"
                }
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ASSIGN_TO_QUEUE,
                    parameters={"queue_name": "shipping_queue"}
                )
            ]
        )

        config = RoutingConfig(rules=[rule], enable_caching=False)
        engine = RoutingEngine(config)

        result = await engine.evaluate(sample_context, sample_decision, sample_metadata)
        assert result is None

    @pytest.mark.asyncio
    async def test_routing_engine_multiple_rules_priority(self, sample_context, sample_decision, sample_metadata):
        """Test that higher priority rules are evaluated first."""
        # Lower priority rule (will match)
        low_priority_rule = RoutingRule(
            name="generic_help_rule",
            priority=50,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.CONTAINS,
                    "value": "help"
                }
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ASSIGN_TO_QUEUE,
                    parameters={"queue_name": "general_queue"}
                )
            ]
        )

        # Higher priority rule (will also match)
        high_priority_rule = RoutingRule(
            name="billing_urgent_rule",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.CONTAINS,
                    "value": "billing"
                }
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ASSIGN_TO_QUEUE,
                    parameters={"queue_name": "billing_queue"}
                )
            ]
        )

        config = RoutingConfig(
            rules=[low_priority_rule, high_priority_rule],
            enable_caching=False
        )
        engine = RoutingEngine(config)

        result = await engine.evaluate(sample_context, sample_decision, sample_metadata)

        assert result is not None
        assert result.rule_name == "billing_urgent_rule"  # Higher priority rule should match
        assert result.get_assigned_queue() == "billing_queue"

    @pytest.mark.asyncio
    async def test_routing_engine_complex_conditions(self, sample_context, sample_decision, sample_metadata):
        """Test rule with multiple conditions (AND logic)."""
        rule = RoutingRule(
            name="premium_billing_rule",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.CONTAINS,
                    "value": "billing"
                },
                {
                    "type": ConditionType.USER_ATTRIBUTE,
                    "field": "tier",
                    "operator": Operator.EQUALS,
                    "value": "premium"
                }
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ASSIGN_TO_AGENT,
                    parameters={"agent_id": "premium-agent-123"}
                )
            ]
        )

        config = RoutingConfig(rules=[rule], enable_caching=False)
        engine = RoutingEngine(config)

        result = await engine.evaluate(sample_context, sample_decision, sample_metadata)

        assert result is not None
        assert result.rule_name == "premium_billing_rule"
        assert result.get_assigned_agent() == "premium-agent-123"

    @pytest.mark.asyncio
    async def test_routing_engine_rule_with_negation(self, sample_context, sample_decision, sample_metadata):
        """Test rule with negated conditions."""
        rule = RoutingRule(
            name="non_basic_user_rule",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.USER_ATTRIBUTE,
                    "field": "tier",
                    "operator": Operator.EQUALS,
                    "value": "basic",
                    "negate": True
                }
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ADD_TAGS,
                    parameters={"tags": ["non_basic"]}
                )
            ]
        )

        config = RoutingConfig(rules=[rule], enable_caching=False)
        engine = RoutingEngine(config)

        result = await engine.evaluate(sample_context, sample_decision, sample_metadata)

        assert result is not None
        assert result.rule_name == "non_basic_user_rule"
        assert "non_basic" in result.get_tags()

    def test_routing_config_management(self):
        """Test routing configuration management."""
        config = RoutingConfig()

        # Add a rule
        rule1 = RoutingRule(
            name="test_rule_1",
            priority=100,
            conditions=[],
            actions=[]
        )
        config.add_rule(rule1)
        assert len(config.rules) == 1

        # Add another rule
        rule2 = RoutingRule(
            name="test_rule_2",
            priority=50,
            conditions=[],
            actions=[]
        )
        config.add_rule(rule2)
        assert len(config.rules) == 2

        # Check priority ordering
        assert config.rules[0].name == "test_rule_1"  # Higher priority
        assert config.rules[1].name == "test_rule_2"  # Lower priority

        # Get rule by name
        found_rule = config.get_rule("test_rule_1")
        assert found_rule is not None
        assert found_rule.name == "test_rule_1"

        # Remove rule
        removed = config.remove_rule("test_rule_1")
        assert removed is True
        assert len(config.rules) == 1

        # Try to add duplicate rule
        with pytest.raises(ValueError, match="Rule with name 'test_rule_2' already exists"):
            config.add_rule(rule2)

    def test_rule_metadata(self):
        """Test rule metadata functionality."""
        rule = RoutingRule(
            name="test_rule",
            priority=100,
            conditions=[],
            actions=[]
        )

        # Check initial state
        assert rule.is_enabled() is True
        assert rule.metadata.version == 1

        # Disable rule
        rule.disable()
        assert rule.is_enabled() is False
        assert rule.metadata.version == 2

        # Enable rule
        rule.enable()
        assert rule.is_enabled() is True
        assert rule.metadata.version == 3

    @pytest.mark.asyncio
    async def test_routing_engine_performance_profiler(self, sample_context, sample_decision, sample_metadata):
        """Test routing engine performance profiler."""
        # Create multiple rules
        rules = []
        for i in range(5):
            rule = RoutingRule(
                name=f"test_rule_{i}",
                priority=100 - i * 10,
                conditions=[
                    {
                        "type": ConditionType.MESSAGE_CONTENT,
                        "field": "content",
                        "operator": Operator.CONTAINS,
                        "value": "test"
                    }
                ],
                actions=[
                    RuleAction(
                        type=RuleActionType.ADD_TAGS,
                        parameters={"tags": [f"tag_{i}"]}
                    )
                ]
            )
            rules.append(rule)

        config = RoutingConfig(rules=rules, enable_caching=False)
        engine = RoutingEngine(config)

        # Run performance profiling
        from handoffkit.routing.engine import RulePerformanceProfiler
        profiler = RulePerformanceProfiler(engine)
        results = await profiler.profile_rules(sample_context, sample_decision, sample_metadata)

        assert "rule_evaluations" in results
        assert "total_evaluation_time_ms" in results
        assert len(results["rule_evaluations"]) == 5

    @pytest.mark.asyncio
    async def test_routing_engine_test_rule(self, sample_context, sample_decision, sample_metadata):
        """Test individual rule testing functionality."""
        rule = RoutingRule(
            name="test_rule",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.CONTAINS,
                    "value": "billing"
                }
            ],
            actions=[]
        )

        config = RoutingConfig(rules=[rule], enable_caching=False)
        engine = RoutingEngine(config)

        # Test the rule
        test_result = await engine.test_rule(rule, sample_context, sample_decision, sample_metadata)

        assert test_result["rule_name"] == "test_rule"
        assert test_result["overall_match"] is True
        assert len(test_result["condition_results"]) == 1
        assert test_result["condition_results"][0]["result"] is True

    @pytest.mark.asyncio
    async def test_routing_engine_caching(self, sample_context, sample_decision, sample_metadata):
        """Test routing engine caching functionality."""
        rule = RoutingRule(
            name="cached_rule",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.CONTAINS,
                    "value": "billing"
                }
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ADD_TAGS,
                    parameters={"tags": ["cached"]}
                )
            ]
        )

        config = RoutingConfig(rules=[rule], enable_caching=True, cache_ttl_seconds=60)
        engine = RoutingEngine(config)

        # First evaluation
        result1 = await engine.evaluate(sample_context, sample_decision, sample_metadata)
        assert result1 is not None

        # Second evaluation should use cache
        result2 = await engine.evaluate(sample_context, sample_decision, sample_metadata)
        assert result2 is not None

        # Check cache stats
        summary = engine.get_rule_summary()
        assert summary["cache_enabled"] is True
        assert summary["cache_size"] > 0