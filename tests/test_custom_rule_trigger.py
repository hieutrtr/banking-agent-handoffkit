"""Tests for CustomRuleTrigger.

This module tests the custom rule engine trigger which allows developers
to define custom IF-THEN-priority rules for domain-specific handoff logic.
"""

import time

import pytest

from handoffkit.core.types import Message, TriggerResult, TriggerType
from handoffkit.triggers.custom_rules import CustomRuleTrigger


class TestCustomRuleTriggerBasic:
    """Basic tests for CustomRuleTrigger evaluate method."""

    @pytest.fixture
    def trigger(self) -> CustomRuleTrigger:
        """Create a CustomRuleTrigger instance with no rules."""
        return CustomRuleTrigger()

    @pytest.mark.asyncio
    async def test_returns_trigger_result(self, trigger: CustomRuleTrigger):
        """Test that evaluate returns a TriggerResult."""
        message = Message(speaker="user", content="Hello")
        result = await trigger.evaluate(message)

        assert isinstance(result, TriggerResult)

    @pytest.mark.asyncio
    async def test_no_rules_does_not_trigger(self, trigger: CustomRuleTrigger):
        """Test that no rules means no trigger."""
        message = Message(speaker="user", content="What is my balance?")
        result = await trigger.evaluate(message)

        assert result.triggered is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_trigger_type_is_custom_rule(self):
        """Test that trigger_type is CUSTOM_RULE when triggered."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "test-rule",
            "name": "Test Rule",
            "condition": {"field": "message.content", "operator": "contains", "value": "urgent"},
            "priority": "high",
        })
        message = Message(speaker="user", content="This is urgent")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.trigger_type == TriggerType.CUSTOM_RULE


class TestSimpleRuleMatching:
    """Tests for simple rule matching (message contains)."""

    @pytest.mark.asyncio
    async def test_message_contains_triggers(self):
        """Test message.content contains condition triggers."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "contains-rule",
            "name": "Contains Account",
            "condition": {"field": "message.content", "operator": "contains", "value": "account"},
            "priority": "high",
        })
        message = Message(speaker="user", content="I need help with my account")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert "account" in result.reason.lower() or "contains-rule" in str(result.metadata)

    @pytest.mark.asyncio
    async def test_message_contains_case_insensitive(self):
        """Test message contains is case-insensitive."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "case-test",
            "name": "Case Test",
            "condition": {"field": "message.content", "operator": "contains", "value": "URGENT"},
            "priority": "high",
        })
        message = Message(speaker="user", content="this is urgent please")
        result = await trigger.evaluate(message)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_message_not_contains_does_not_trigger(self):
        """Test message not containing keyword doesn't trigger."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "no-match",
            "name": "No Match",
            "condition": {"field": "message.content", "operator": "contains", "value": "urgent"},
            "priority": "high",
        })
        message = Message(speaker="user", content="Just a normal question")
        result = await trigger.evaluate(message)

        assert result.triggered is False


class TestRegexMatching:
    """Tests for regex pattern matching."""

    @pytest.mark.asyncio
    async def test_message_matches_regex(self):
        """Test message.content matches regex condition."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "regex-rule",
            "name": "Order Number Pattern",
            "condition": {"field": "message.content", "operator": "matches", "value": r"order\s*#?\d+"},
            "priority": "medium",
        })
        message = Message(speaker="user", content="Where is my order #12345?")
        result = await trigger.evaluate(message)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_message_matches_regex_no_match(self):
        """Test message not matching regex doesn't trigger."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "regex-rule",
            "name": "Email Pattern",
            "condition": {"field": "message.content", "operator": "matches", "value": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"},
            "priority": "medium",
        })
        message = Message(speaker="user", content="My email is broken")
        result = await trigger.evaluate(message)

        assert result.triggered is False


class TestCompoundConditions:
    """Tests for AND/OR compound conditions."""

    @pytest.mark.asyncio
    async def test_and_condition_all_match(self):
        """Test AND condition - all must match to trigger."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "and-rule",
            "name": "AND Rule",
            "condition": {
                "operator": "AND",
                "conditions": [
                    {"field": "message.content", "operator": "contains", "value": "account"},
                    {"field": "message.content", "operator": "contains", "value": "help"},
                ]
            },
            "priority": "high",
        })
        message = Message(speaker="user", content="I need help with my account")
        result = await trigger.evaluate(message)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_and_condition_partial_match(self):
        """Test AND condition - partial match doesn't trigger."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "and-rule",
            "name": "AND Rule",
            "condition": {
                "operator": "AND",
                "conditions": [
                    {"field": "message.content", "operator": "contains", "value": "account"},
                    {"field": "message.content", "operator": "contains", "value": "urgent"},
                ]
            },
            "priority": "high",
        })
        message = Message(speaker="user", content="I need help with my account")
        result = await trigger.evaluate(message)

        assert result.triggered is False

    @pytest.mark.asyncio
    async def test_or_condition_one_match(self):
        """Test OR condition - one match is enough to trigger."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "or-rule",
            "name": "OR Rule",
            "condition": {
                "operator": "OR",
                "conditions": [
                    {"field": "message.content", "operator": "contains", "value": "urgent"},
                    {"field": "message.content", "operator": "contains", "value": "emergency"},
                ]
            },
            "priority": "immediate",
        })
        message = Message(speaker="user", content="This is an emergency")
        result = await trigger.evaluate(message)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_or_condition_no_match(self):
        """Test OR condition - no match doesn't trigger."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "or-rule",
            "name": "OR Rule",
            "condition": {
                "operator": "OR",
                "conditions": [
                    {"field": "message.content", "operator": "contains", "value": "urgent"},
                    {"field": "message.content", "operator": "contains", "value": "emergency"},
                ]
            },
            "priority": "immediate",
        })
        message = Message(speaker="user", content="Just a normal question")
        result = await trigger.evaluate(message)

        assert result.triggered is False


class TestContextConditions:
    """Tests for context-based conditions."""

    @pytest.mark.asyncio
    async def test_context_equals(self):
        """Test context field equals condition."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "tier-rule",
            "name": "Premium User",
            "condition": {"field": "context.user_tier", "operator": "==", "value": "premium"},
            "priority": "high",
        })
        message = Message(speaker="user", content="Hello")
        context = {"user_tier": "premium"}
        result = await trigger.evaluate(message, context=context)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_context_not_equals(self):
        """Test context field not equals condition."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "tier-rule",
            "name": "Non-Premium",
            "condition": {"field": "context.user_tier", "operator": "!=", "value": "standard"},
            "priority": "medium",
        })
        message = Message(speaker="user", content="Hello")
        context = {"user_tier": "premium"}
        result = await trigger.evaluate(message, context=context)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_context_greater_than(self):
        """Test context field greater than condition."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "value-rule",
            "name": "High Value Order",
            "condition": {"field": "context.order_value", "operator": ">", "value": 1000},
            "priority": "high",
        })
        message = Message(speaker="user", content="Where is my order?")
        context = {"order_value": 1500}
        result = await trigger.evaluate(message, context=context)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_context_less_than(self):
        """Test context field less than condition."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "sentiment-rule",
            "name": "Low Sentiment",
            "condition": {"field": "context.sentiment_score", "operator": "<", "value": 0.3},
            "priority": "high",
        })
        message = Message(speaker="user", content="This is frustrating")
        context = {"sentiment_score": 0.2}
        result = await trigger.evaluate(message, context=context)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_context_missing_key(self):
        """Test missing context key returns False (no error)."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "tier-rule",
            "name": "Premium User",
            "condition": {"field": "context.user_tier", "operator": "==", "value": "premium"},
            "priority": "high",
        })
        message = Message(speaker="user", content="Hello")
        context = {}  # No user_tier key
        result = await trigger.evaluate(message, context=context)

        assert result.triggered is False


class TestConversationConditions:
    """Tests for conversation-based conditions."""

    @pytest.mark.asyncio
    async def test_conversation_length_greater_than(self):
        """Test conversation.length greater than condition."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "length-rule",
            "name": "Long Conversation",
            "condition": {"field": "conversation.length", "operator": ">", "value": 5},
            "priority": "medium",
        })
        message = Message(speaker="user", content="Hello")
        history = [Message(speaker="user", content=f"Message {i}") for i in range(6)]
        result = await trigger.evaluate(message, history=history)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_conversation_length_short(self):
        """Test short conversation doesn't trigger length rule."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "length-rule",
            "name": "Long Conversation",
            "condition": {"field": "conversation.length", "operator": ">", "value": 10},
            "priority": "medium",
        })
        message = Message(speaker="user", content="Hello")
        history = [Message(speaker="user", content=f"Message {i}") for i in range(3)]
        result = await trigger.evaluate(message, history=history)

        assert result.triggered is False


class TestPriorityOrdering:
    """Tests for priority ordering (highest priority wins)."""

    @pytest.mark.asyncio
    async def test_highest_priority_wins(self):
        """Test that highest priority matching rule is selected."""
        trigger = CustomRuleTrigger()
        # Add low priority rule first
        trigger.add_rule({
            "id": "low-rule",
            "name": "Low Priority",
            "condition": {"field": "message.content", "operator": "contains", "value": "help"},
            "priority": "low",
        })
        # Add high priority rule second
        trigger.add_rule({
            "id": "high-rule",
            "name": "High Priority",
            "condition": {"field": "message.content", "operator": "contains", "value": "help"},
            "priority": "high",
        })
        message = Message(speaker="user", content="I need help")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.metadata.get("matched_rule_id") == "high-rule"

    @pytest.mark.asyncio
    async def test_immediate_priority_highest(self):
        """Test that immediate priority beats all others."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "high-rule",
            "name": "High Priority",
            "condition": {"field": "message.content", "operator": "contains", "value": "account"},
            "priority": "high",
        })
        trigger.add_rule({
            "id": "immediate-rule",
            "name": "Immediate Priority",
            "condition": {"field": "message.content", "operator": "contains", "value": "account"},
            "priority": "immediate",
        })
        message = Message(speaker="user", content="My account is compromised")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.metadata.get("matched_rule_id") == "immediate-rule"

    @pytest.mark.asyncio
    async def test_all_matching_rules_in_metadata(self):
        """Test that all matching rules are logged in metadata."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "rule-1",
            "name": "Rule 1",
            "condition": {"field": "message.content", "operator": "contains", "value": "help"},
            "priority": "low",
        })
        trigger.add_rule({
            "id": "rule-2",
            "name": "Rule 2",
            "condition": {"field": "message.content", "operator": "contains", "value": "help"},
            "priority": "medium",
        })
        message = Message(speaker="user", content="I need help")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        matched_rules = result.metadata.get("matched_rules", [])
        assert len(matched_rules) == 2


class TestRuleManagement:
    """Tests for rule management (add/remove)."""

    def test_add_rule(self):
        """Test add_rule adds rules dynamically."""
        trigger = CustomRuleTrigger()
        assert len(trigger.get_rules()) == 0

        trigger.add_rule({
            "id": "new-rule",
            "name": "New Rule",
            "condition": {"field": "message.content", "operator": "contains", "value": "test"},
            "priority": "medium",
        })
        assert len(trigger.get_rules()) == 1

    def test_remove_rule_success(self):
        """Test remove_rule returns True when rule found."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "to-remove",
            "name": "To Remove",
            "condition": {"field": "message.content", "operator": "contains", "value": "test"},
            "priority": "medium",
        })
        assert len(trigger.get_rules()) == 1

        result = trigger.remove_rule("to-remove")
        assert result is True
        assert len(trigger.get_rules()) == 0

    def test_remove_rule_not_found(self):
        """Test remove_rule returns False when rule not found."""
        trigger = CustomRuleTrigger()
        result = trigger.remove_rule("nonexistent")
        assert result is False

    def test_get_rules(self):
        """Test get_rules returns all rules."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({"id": "rule-1", "name": "Rule 1", "condition": {}, "priority": "low"})
        trigger.add_rule({"id": "rule-2", "name": "Rule 2", "condition": {}, "priority": "high"})

        rules = trigger.get_rules()
        assert len(rules) == 2

    def test_auto_generate_rule_id(self):
        """Test rule ID is auto-generated if not provided."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "name": "No ID Rule",
            "condition": {"field": "message.content", "operator": "contains", "value": "test"},
            "priority": "medium",
        })
        rules = trigger.get_rules()
        assert len(rules) == 1
        assert rules[0].get("id") is not None


class TestDisabledRules:
    """Tests for disabled rules."""

    @pytest.mark.asyncio
    async def test_disabled_rule_not_evaluated(self):
        """Test that disabled rules are not evaluated."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "disabled-rule",
            "name": "Disabled Rule",
            "condition": {"field": "message.content", "operator": "contains", "value": "help"},
            "priority": "high",
            "enabled": False,
        })
        message = Message(speaker="user", content="I need help")
        result = await trigger.evaluate(message)

        assert result.triggered is False


class TestPerformance:
    """Tests for performance requirements."""

    @pytest.fixture
    def trigger_with_rules(self) -> CustomRuleTrigger:
        """Create a trigger with multiple rules."""
        trigger = CustomRuleTrigger()
        for i in range(10):
            trigger.add_rule({
                "id": f"rule-{i}",
                "name": f"Rule {i}",
                "condition": {"field": "message.content", "operator": "contains", "value": f"keyword{i}"},
                "priority": "medium",
            })
        return trigger

    @pytest.mark.asyncio
    async def test_evaluation_under_100ms(self, trigger_with_rules: CustomRuleTrigger):
        """Test that evaluation completes in <100ms."""
        message = Message(speaker="user", content="Test message with keyword5")

        start_time = time.perf_counter()
        result = await trigger_with_rules.evaluate(message)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 100, f"Evaluation took {elapsed_ms:.2f}ms, expected <100ms"

    @pytest.mark.asyncio
    async def test_duration_in_metadata(self):
        """Test that duration_ms is included in result metadata."""
        trigger = CustomRuleTrigger()
        message = Message(speaker="user", content="Hello")
        result = await trigger.evaluate(message)

        assert "duration_ms" in result.metadata
        assert isinstance(result.metadata["duration_ms"], float)
        assert result.metadata["duration_ms"] >= 0


class TestMetadata:
    """Tests for metadata in trigger results."""

    @pytest.mark.asyncio
    async def test_matched_rule_info_in_metadata(self):
        """Test that matched rule info is in metadata."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "info-rule",
            "name": "Info Rule",
            "condition": {"field": "message.content", "operator": "contains", "value": "test"},
            "priority": "high",
        })
        message = Message(speaker="user", content="This is a test")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert "matched_rule_id" in result.metadata
        assert result.metadata["matched_rule_id"] == "info-rule"

    @pytest.mark.asyncio
    async def test_priority_in_metadata(self):
        """Test that priority is included in metadata."""
        trigger = CustomRuleTrigger()
        trigger.add_rule({
            "id": "priority-rule",
            "name": "Priority Rule",
            "condition": {"field": "message.content", "operator": "contains", "value": "urgent"},
            "priority": "immediate",
        })
        message = Message(speaker="user", content="This is urgent")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.metadata.get("priority") == "immediate"


class TestTriggerProperties:
    """Tests for trigger properties."""

    def test_trigger_name(self):
        """Test that trigger_name property returns correct value."""
        trigger = CustomRuleTrigger()
        assert trigger.trigger_name == "custom_rule"

    def test_init_with_rules(self):
        """Test initialization with rules list."""
        rules = [
            {"id": "rule-1", "name": "Rule 1", "condition": {}, "priority": "low"},
        ]
        trigger = CustomRuleTrigger(rules=rules)
        assert len(trigger.get_rules()) == 1

    def test_init_without_rules(self):
        """Test initialization without rules."""
        trigger = CustomRuleTrigger()
        assert len(trigger.get_rules()) == 0
