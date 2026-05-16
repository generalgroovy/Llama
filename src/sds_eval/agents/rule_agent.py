from __future__ import annotations

import re
from typing import Any

from sds_eval.agents.base import AgentAdapter, AgentContext, AgentResponse
from sds_eval.task.planner import next_action_for_path, shortest_path


class RuleAgent(AgentAdapter):
    """Deterministic SDS agent that maps instruction text to navigation actions."""

    KEYWORDS = {
        "north": ("north", "up"),
        "south": ("south", "down"),
        "east": ("east", "right"),
        "west": ("west", "left"),
        "stay": ("stay", "wait"),
        "clarify": ("clarify", "unclear", "repeat", "closer"),
    }

    def __init__(self, name: str = "RuleAgent", metadata: dict | None = None):
        super().__init__(name, metadata or {"role": "deterministic_sds"})

    def respond(self, context: AgentContext) -> AgentResponse:
        if context.private_context.get("network"):
            return self._respond_as_network_planner(context)
        instruction = (context.last_instruction or "").lower()
        action = "clarify"
        for candidate, words in self.KEYWORDS.items():
            if any(word in instruction for word in words):
                action = candidate
                break
        return AgentResponse(text=f"Interpreted action: {action}", interpreted_action=action)

    def _respond_as_network_planner(self, context: AgentContext) -> AgentResponse:
        network = context.private_context["network"]
        instruction = context.last_instruction or ""
        belief_before = dict(context.shared_state.get("b_belief", {}))
        goal = _resolve_goal(instruction, network) or belief_before.get("goal")
        constraints = _resolve_constraints(instruction) or list(belief_before.get("constraints", []))
        belief_after = {"goal": goal, "constraints": constraints}

        if not goal:
            return AgentResponse(
                text="I need the destination before I can calculate a route.",
                interpreted_action="clarify",
                metadata={
                    "dialogue_act": "clarification_request",
                    "intent": "request_missing_goal",
                    "belief_state_before": belief_before,
                    "belief_state_after": belief_after,
                    "ambiguity_detected": True,
                    "repair_or_clarification": True,
                },
            )

        path, diagnostics = shortest_path(network, context.state["position"], goal, constraints)
        if not path:
            return AgentResponse(
                text="No valid route satisfies the communicated constraints.",
                interpreted_action="stop",
                metadata={
                    "dialogue_act": "failure_report",
                    "intent": "report_no_valid_route",
                    "interpreted_goal": goal,
                    "interpreted_constraints": constraints,
                    "belief_state_before": belief_before,
                    "belief_state_after": belief_after,
                    "route_plan": [],
                    "route_diagnostics": diagnostics,
                    "constraint_satisfied": False,
                },
            )

        action = next_action_for_path(path)
        label = _goal_label(goal, network)
        return AgentResponse(
            text=f"Route step: {action} toward {label}. Planned remaining steps: {max(0, len(path) - 1)}.",
            interpreted_action=action,
            metadata={
                "dialogue_act": "route_proposal",
                "intent": "calculate_and_execute_next_route_step",
                "interpreted_goal": goal,
                "interpreted_constraints": constraints,
                "proposed_action": action,
                "selected_action": action,
                "route_plan": path,
                "route_diagnostics": diagnostics,
                "constraint_satisfied": True,
                "belief_state_before": belief_before,
                "belief_state_after": belief_after,
                "ambiguity_detected": False,
                "repair_or_clarification": False,
            },
        )


def _resolve_goal(text: str, network: dict[str, Any]) -> list[int] | None:
    lowered = text.lower()
    for label, position in network.get("landmarks", {}).items():
        if label.lower() in lowered:
            return list(position)
    match = re.search(r"\[(\d+),\s*(\d+)\]", lowered)
    if match:
        return [int(match.group(1)), int(match.group(2))]
    return None


def _resolve_constraints(text: str) -> list[str]:
    lowered = text.lower()
    constraints: list[str] = []
    if "avoid" in lowered or "blocked" in lowered or "obstacle" in lowered:
        constraints.append("avoid_blocked")
    if "short" in lowered:
        constraints.append("prefer_shortest")
    return constraints


def _goal_label(goal: list[int], network: dict[str, Any]) -> str:
    for label, position in network.get("landmarks", {}).items():
        if list(position) == list(goal):
            return label
    return str(goal)
