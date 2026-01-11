"""Action execution system for routing rules."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional

from handoffkit.core.types import ConversationContext, HandoffDecision
from handoffkit.routing.models import RuleAction, RoutingResult
from handoffkit.routing.types import RuleActionType
from handoffkit.utils.logging import get_logger


class ActionExecutor:
    """Executes routing rule actions."""

    def __init__(self):
        """Initialize action executor."""
        self._logger = get_logger("routing.actions")
        self._action_handlers = {
            RuleActionType.ASSIGN_TO_AGENT: AssignToAgentAction(),
            RuleActionType.ASSIGN_TO_QUEUE: AssignToQueueAction(),
            RuleActionType.ASSIGN_TO_DEPARTMENT: AssignToDepartmentAction(),
            RuleActionType.SET_PRIORITY: SetPriorityAction(),
            RuleActionType.ADD_TAGS: AddTagsAction(),
            RuleActionType.REMOVE_TAGS: RemoveTagsAction(),
            RuleActionType.SET_CUSTOM_FIELD: SetCustomFieldAction(),
            RuleActionType.ROUTE_TO_FALLBACK: RouteToFallbackAction(),
        }

    async def execute_actions(
        self,
        actions: list[RuleAction],
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> RoutingResult:
        """Execute a list of actions.

        Args:
            actions: List of actions to execute
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            RoutingResult with execution details
        """
        try:
            self._logger.info(
                "Executing routing actions",
                extra={"action_count": len(actions)},
            )

            start_time = asyncio.get_event_loop().time()
            executed_actions = []
            routing_decision = "continue"
            action_metadata = {}

            # Execute actions in order
            for i, action in enumerate(actions):
                try:
                    handler = self._action_handlers.get(action.type)
                    if not handler:
                        self._logger.warning(
                            f"No handler for action type: {action.type}",
                            extra={"action_type": action.type},
                        )
                        continue

                    # Execute the action
                    result = await handler.execute(action, context, decision, metadata)
                    executed_actions.append(action)

                    # Update routing decision if needed
                    if result.decision != "continue":
                        routing_decision = result.decision

                    # Collect metadata
                    if result.metadata:
                        action_metadata[f"action_{i}"] = result.metadata

                    self._logger.info(
                        f"Executed action: {action.type}",
                        extra={
                            "action_type": action.type,
                            "success": result.success,
                            "decision": result.decision,
                        },
                    )

                except Exception as e:
                    self._logger.error(
                        f"Failed to execute action: {e}",
                        extra={
                            "action_type": action.type,
                            "error": str(e),
                        },
                    )
                    # Continue with other actions on failure

            # Calculate execution time
            execution_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            self._logger.info(
                "Completed routing actions",
                extra={
                    "executed_count": len(executed_actions),
                    "routing_decision": routing_decision,
                    "execution_time_ms": execution_time_ms,
                },
            )

            return RoutingResult(
                rule_name="routing_actions",  # Will be set by caller
                actions_applied=executed_actions,
                routing_decision=routing_decision,
                metadata=action_metadata,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._logger.error(
                f"Action execution failed: {e}",
                extra={"error": str(e)},
            )
            # Return fallback result
            return RoutingResult(
                rule_name="routing_actions",
                actions_applied=[],
                routing_decision="continue",
                metadata={"error": str(e)},
                execution_time_ms=0,
            )


class ActionHandler(ABC):
    """Base class for action handlers."""

    @abstractmethod
    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> "ActionResult":
        """Execute the action.

        Args:
            action: The action to execute
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            ActionResult with execution details
        """
        pass


class ActionResult:
    """Result of action execution."""

    def __init__(
        self,
        success: bool,
        decision: str = "continue",
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Initialize action result.

        Args:
            success: Whether action succeeded
            decision: Routing decision (continue, assigned, fallback)
            metadata: Additional metadata
        """
        self.success = success
        self.decision = decision
        self.metadata = metadata or {}


class AssignToAgentAction(ActionHandler):
    """Assign handoff to a specific agent."""

    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> ActionResult:
        """Assign to specific agent."""
        try:
            agent_id = action.get_agent_id()
            if not agent_id:
                return ActionResult(
                    success=False,
                    metadata={"error": "No agent_id specified"},
                )

            # Store assignment in metadata
            metadata["routing_assignment"] = {
                "type": "agent",
                "agent_id": agent_id,
                "method": "rule_based",
            }

            return ActionResult(
                success=True,
                decision="assigned",
                metadata={
                    "agent_id": agent_id,
                    "assignment_type": "specific_agent",
                },
            )

        except Exception as e:
            return ActionResult(
                success=False,
                metadata={"error": str(e)},
            )


class AssignToQueueAction(ActionHandler):
    """Assign handoff to a queue."""

    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> ActionResult:
        """Assign to queue."""
        try:
            queue_name = action.get_queue_name()
            if not queue_name:
                return ActionResult(
                    success=False,
                    metadata={"error": "No queue_name specified"},
                )

            # Store assignment in metadata
            metadata["routing_assignment"] = {
                "type": "queue",
                "queue_name": queue_name,
                "method": "rule_based",
            }

            return ActionResult(
                success=True,
                metadata={
                    "queue_name": queue_name,
                    "assignment_type": "queue",
                },
            )

        except Exception as e:
            return ActionResult(
                success=False,
                metadata={"error": str(e)},
            )


class AssignToDepartmentAction(ActionHandler):
    """Assign handoff to a department."""

    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> ActionResult:
        """Assign to department."""
        try:
            department = action.get_department()
            if not department:
                return ActionResult(
                    success=False,
                    metadata={"error": "No department specified"},
                )

            # Store assignment in metadata
            metadata["routing_assignment"] = {
                "type": "department",
                "department": department,
                "method": "rule_based",
            }

            return ActionResult(
                success=True,
                metadata={
                    "department": department,
                    "assignment_type": "department",
                },
            )

        except Exception as e:
            return ActionResult(
                success=False,
                metadata={"error": str(e)},
            )


class SetPriorityAction(ActionHandler):
    """Set handoff priority."""

    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> ActionResult:
        """Set priority."""
        try:
            priority = action.get_priority()
            if not priority:
                return ActionResult(
                    success=False,
                    metadata={"error": "Invalid or missing priority"},
                )

            # Update decision priority - import here to avoid circular imports
            from handoffkit.core.types import HandoffPriority
            try:
                priority_enum = HandoffPriority(priority)
                decision.priority = priority_enum
            except ValueError:
                return ActionResult(
                    success=False,
                    metadata={"error": f"Invalid priority value: {priority}"},
                )

            # Store in metadata
            metadata["routing_priority"] = {
                "priority": priority,
                "set_by": "rule",
            }

            return ActionResult(
                success=True,
                metadata={
                    "priority": priority,
                    "action": "set_priority",
                },
            )

        except Exception as e:
            return ActionResult(
                success=False,
                metadata={"error": str(e)},
            )


class AddTagsAction(ActionHandler):
    """Add tags to handoff."""

    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> ActionResult:
        """Add tags."""
        try:
            tags = action.get_tags()
            if not tags:
                return ActionResult(
                    success=True,  # No tags to add is not an error
                    metadata={"tags_added": []},
                )

            # Get existing tags or initialize
            existing_tags = metadata.get("routing_tags", [])
            if not isinstance(existing_tags, list):
                existing_tags = []

            # Add new tags (avoid duplicates)
            tags_added = []
            for tag in tags:
                if tag and tag not in existing_tags:
                    existing_tags.append(tag)
                    tags_added.append(tag)

            # Update metadata
            metadata["routing_tags"] = existing_tags

            return ActionResult(
                success=True,
                metadata={
                    "tags_added": tags_added,
                    "total_tags": len(existing_tags),
                },
            )

        except Exception as e:
            return ActionResult(
                success=False,
                metadata={"error": str(e)},
            )


class RemoveTagsAction(ActionHandler):
    """Remove tags from handoff."""

    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> ActionResult:
        """Remove tags."""
        try:
            tags_to_remove = action.get_tags()
            if not tags_to_remove:
                return ActionResult(
                    success=True,  # No tags to remove is not an error
                    metadata={"tags_removed": []},
                )

            # Get existing tags
            existing_tags = metadata.get("routing_tags", [])
            if not isinstance(existing_tags, list):
                existing_tags = []

            # Remove tags
            tags_removed = []
            for tag in tags_to_remove:
                if tag and tag in existing_tags:
                    existing_tags.remove(tag)
                    tags_removed.append(tag)

            # Update metadata
            metadata["routing_tags"] = existing_tags

            return ActionResult(
                success=True,
                metadata={
                    "tags_removed": tags_removed,
                    "total_tags": len(existing_tags),
                },
            )

        except Exception as e:
            return ActionResult(
                success=False,
                metadata={"error": str(e)},
            )


class SetCustomFieldAction(ActionHandler):
    """Set custom field value."""

    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> ActionResult:
        """Set custom field."""
        try:
            field_name, field_value = action.get_custom_field()
            if not field_name:
                return ActionResult(
                    success=False,
                    metadata={"error": "No field name specified"},
                )

            # Initialize custom fields if needed
            if "routing_custom_fields" not in metadata:
                metadata["routing_custom_fields"] = {}

            # Set field value
            metadata["routing_custom_fields"][field_name] = field_value

            return ActionResult(
                success=True,
                metadata={
                    "field_name": field_name,
                    "field_value": field_value,
                    "action": "set_custom_field",
                },
            )

        except Exception as e:
            return ActionResult(
                success=False,
                metadata={"error": str(e)},
            )


class RouteToFallbackAction(ActionHandler):
    """Route to fallback system."""

    async def execute(
        self,
        action: RuleAction,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> ActionResult:
        """Route to fallback."""
        try:
            reason = action.parameters.get("reason", "rule_based_fallback")

            # Store fallback routing in metadata
            metadata["routing_fallback"] = {
                "triggered": True,
                "reason": reason,
                "triggered_by": "routing_rule",
            }

            return ActionResult(
                success=True,
                decision="fallback",
                metadata={
                    "fallback_reason": reason,
                    "action": "route_to_fallback",
                },
            )

        except Exception as e:
            return ActionResult(
                success=False,
                metadata={"error": str(e)},
            )