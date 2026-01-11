"""Rule evaluation engine for routing decisions."""

import asyncio
import time
from typing import Any, Optional

from handoffkit.core.types import ConversationContext, HandoffDecision
from handoffkit.routing.actions import ActionExecutor
from handoffkit.routing.conditions import Condition, ConditionEvaluator
from handoffkit.routing.models import RoutingResult, RoutingRule
from handoffkit.utils.logging import get_logger


class RoutingEngine:
    """Engine for evaluating routing rules.

    Evaluates a set of routing rules against conversation context to determine
    the appropriate routing actions. Rules are evaluated in priority order,
    and the first matching rule's actions are executed.
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize routing engine.

        Args:
            config: Routing configuration with rules
        """
        # Import here to avoid circular imports
        from handoffkit.routing.models import RoutingConfig
        self.config = config or RoutingConfig()
        self._condition_evaluator = ConditionEvaluator()
        self._action_executor = ActionExecutor()
        self._logger = get_logger("routing.engine")
        self._rule_cache: dict[str, list[bool]] = {}  # Cache condition results per rule
        self._cache_ttl = self.config.cache_ttl_seconds
        self._last_cache_clear = time.time()

    def update_config(self, config: Any) -> None:
        """Update routing configuration.

        Args:
            config: New routing configuration
        """
        self.config = config
        self._cache_ttl = config.cache_ttl_seconds
        self.clear_cache()

    def clear_cache(self) -> None:
        """Clear the rule evaluation cache."""
        self._rule_cache.clear()
        self._last_cache_clear = time.time()

    async def evaluate(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> Optional[RoutingResult]:
        """Evaluate routing rules against context.

        Args:
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            RoutingResult if a rule matches, None otherwise
        """
        try:
            start_time = time.time()

            # Get enabled rules sorted by priority
            rules = self.config.get_enabled_rules()
            if not rules:
                self._logger.debug("No enabled routing rules to evaluate")
                return None

            self._logger.info(
                "Evaluating routing rules",
                extra={"rule_count": len(rules)},
            )

            # Clean cache if TTL expired
            if self.config.enable_caching and time.time() - self._last_cache_clear > self._cache_ttl:
                self.clear_cache()

            # Evaluate each rule in priority order
            for rule in rules:
                try:
                    # Check if rule matches
                    matches = await self._evaluate_rule(rule, context, decision, metadata)

                    if matches:
                        self._logger.info(
                            f"Rule matched: {rule.name}",
                            extra={
                                "rule_name": rule.name,
                                "rule_priority": rule.priority,
                            },
                        )

                        # Execute rule actions
                        result = await self._execute_rule_actions(
                            rule, context, decision, metadata
                        )
                        result.rule_name = rule.name

                        # Log timing
                        execution_time_ms = (time.time() - start_time) * 1000
                        result.execution_time_ms = execution_time_ms

                        self._logger.info(
                            "Routing rule evaluation completed",
                            extra={
                                "matched_rule": rule.name,
                                "execution_time_ms": execution_time_ms,
                                "actions_applied": len(result.actions_applied),
                            },
                        )

                        return result

                except Exception as e:
                    self._logger.error(
                        f"Error evaluating rule {rule.name}: {e}",
                        extra={
                            "rule_name": rule.name,
                            "error": str(e),
                        },
                    )
                    # Continue with next rule on error

            # No matching rules
            self._logger.debug("No routing rules matched")
            return None

        except Exception as e:
            self._logger.error(
                f"Routing evaluation failed: {e}",
                extra={"error": str(e)},
            )
            return None

    async def _evaluate_rule(
        self,
        rule: RoutingRule,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> bool:
        """Evaluate if a rule matches.

        Args:
            rule: The rule to evaluate
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            True if rule matches, False otherwise
        """
        # Check cache if enabled
        cache_key = f"{rule.name}:{context.conversation_id}"
        if self.config.enable_caching and cache_key in self._rule_cache:
            cached_results = self._rule_cache[cache_key]
            # All conditions must match (AND logic)
            return all(cached_results)

        # Evaluate all conditions (AND logic)
        condition_results = []
        for i, condition_data in enumerate(rule.conditions):
            try:
                # Create condition object
                condition = Condition(**condition_data)

                # Evaluate condition
                matches = await condition.evaluate(context, decision, metadata)
                condition_results.append(matches)

                if self.config.log_evaluations:
                    self._logger.debug(
                        f"Condition {i} evaluation: {matches}",
                        extra={
                            "rule_name": rule.name,
                            "condition_index": i,
                            "condition_type": condition.type.value,
                            "result": matches,
                        },
                    )

                # Short-circuit on first failure (AND logic)
                if not matches:
                    break

            except Exception as e:
                self._logger.error(
                    f"Error evaluating condition {i} in rule {rule.name}: {e}",
                    extra={
                        "rule_name": rule.name,
                        "condition_index": i,
                        "error": str(e),
                    },
                )
                condition_results.append(False)
                break

        # Cache results if enabled
        if self.config.enable_caching:
            self._rule_cache[cache_key] = condition_results

        # All conditions must match
        return all(condition_results)

    async def _execute_rule_actions(
        self,
        rule: RoutingRule,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> RoutingResult:
        """Execute actions for a matching rule.

        Args:
            rule: The matching rule
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            RoutingResult with execution details
        """
        try:
            self._logger.info(
                f"Executing actions for rule: {rule.name}",
                extra={
                    "rule_name": rule.name,
                    "action_count": len(rule.actions),
                },
            )

            # Execute actions
            result = await self._action_executor.execute_actions(
                rule.actions, context, decision, metadata
            )

            # Add rule metadata
            result.metadata.update({
                "rule_name": rule.name,
                "rule_priority": rule.priority,
                "execution_source": "routing_rule",
            })

            return result

        except Exception as e:
            self._logger.error(
                f"Error executing actions for rule {rule.name}: {e}",
                extra={
                    "rule_name": rule.name,
                    "error": str(e),
                },
            )

            # Return fallback result on error
            return RoutingResult(
                rule_name=rule.name,
                actions_applied=[],
                routing_decision="continue",
                metadata={"error": str(e)},
                execution_time_ms=0,
            )

    def get_rule_summary(self) -> dict[str, Any]:
        """Get summary of routing rules.

        Returns:
            Dictionary with rule statistics
        """
        enabled_rules = self.config.get_enabled_rules()
        return {
            "total_rules": len(self.config.rules),
            "enabled_rules": len(enabled_rules),
            "cache_enabled": self.config.enable_caching,
            "cache_size": len(self._rule_cache),
            "max_evaluation_time_ms": self.config.max_evaluation_time_ms,
        }

    async def test_rule(
        self,
        rule: RoutingRule,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Test a rule against context (dry run).

        Args:
            rule: Rule to test
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            Test results with detailed information
        """
        try:
            start_time = time.time()
            condition_results = []

            # Evaluate each condition
            for i, condition_data in enumerate(rule.conditions):
                try:
                    condition = Condition(**condition_data)
                    matches = await condition.evaluate(context, decision, metadata)

                    condition_results.append({
                        "index": i,
                        "type": condition.type.value,
                        "field": condition.field,
                        "operator": condition.operator.value,
                        "value": str(condition.value) if condition.value is not None else None,
                        "result": matches,
                        "extracted_value": str(await condition._extract_value(context, decision, metadata)),
                    })

                except Exception as e:
                    condition_results.append({
                        "index": i,
                        "error": str(e),
                        "result": False,
                    })

            # Overall result
            overall_matches = all(cr.get("result", False) for cr in condition_results)
            execution_time_ms = (time.time() - start_time) * 1000

            return {
                "rule_name": rule.name,
                "overall_match": overall_matches,
                "condition_results": condition_results,
                "execution_time_ms": execution_time_ms,
                "enabled": rule.is_enabled(),
                "priority": rule.priority,
            }

        except Exception as e:
            return {
                "rule_name": rule.name,
                "error": str(e),
                "overall_match": False,
            }

    def validate_configuration(self) -> list[str]:
        """Validate routing configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for duplicate rule names
        names = [rule.name for rule in self.config.rules]
        if len(names) != len(set(names)):
            errors.append("Duplicate rule names found")

        # Validate each rule
        for rule in self.config.rules:
            try:
                # Basic validation happens in model
                pass
            except Exception as e:
                errors.append(f"Rule '{rule.name}' is invalid: {e}")

        # Check for conflicting actions
        for rule in self.config.rules:
            assignment_actions = [a for a in rule.actions if a.type in [
                "assign_to_agent",
                "assign_to_queue",
                "assign_to_department",
            ]]
            if len(assignment_actions) > 1:
                errors.append(f"Rule '{rule.name}' has multiple assignment actions")

        return errors


class RulePerformanceProfiler:
    """Profiles routing rule performance."""

    def __init__(self, engine: RoutingEngine):
        """Initialize profiler.

        Args:
            engine: Routing engine to profile
        """
        self.engine = engine
        self._logger = get_logger("routing.profiler")

    async def profile_rules(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Profile rule evaluation performance.

        Args:
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            Performance profiling results
        """
        try:
            results = {
                "rule_evaluations": [],
                "total_evaluation_time_ms": 0,
                "matching_rule": None,
                "cache_stats": {},
            }

            start_time = time.time()

            # Test each rule individually
            for rule in self.engine.config.rules:
                if not rule.is_enabled():
                    continue

                rule_start = time.time()
                test_result = await self.engine.test_rule(rule, context, decision, metadata)
                rule_time_ms = (time.time() - rule_start) * 1000

                results["rule_evaluations"].append({
                    "rule_name": rule.name,
                    "priority": rule.priority,
                    "execution_time_ms": rule_time_ms,
                    "matched": test_result.get("overall_match", False),
                    "condition_count": len(rule.conditions),
                    "action_count": len(rule.actions),
                })

            # Run full evaluation
            full_start = time.time()
            result = await self.engine.evaluate(context, decision, metadata)
            full_time_ms = (time.time() - full_start) * 1000

            results["total_evaluation_time_ms"] = full_time_ms
            results["matching_rule"] = result.rule_name if result else None
            results["cache_stats"] = self.engine.get_rule_summary()

            # Log slow rules
            slow_rules = [
                r for r in results["rule_evaluations"]
                if r["execution_time_ms"] > 50  # Flag rules taking >50ms
            ]
            if slow_rules:
                self._logger.warning(
                    f"Found {len(slow_rules)} slow routing rules",
                    extra={"slow_rules": [r["rule_name"] for r in slow_rules]},
                )

            return results

        except Exception as e:
            self._logger.error(
                f"Rule profiling failed: {e}",
                extra={"error": str(e)},
            )
            return {"error": str(e)}