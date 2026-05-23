from __future__ import annotations

import re
from typing import Any

from sds_eval.agents.base import AgentAdapter, AgentContext, AgentResponse
from sds_eval.task.planner import next_action_for_path, route_advice_text, shortest_path, summarize_route_segments


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
        prompt_policy = context.parameters.get("prompt_policy", {})
        planning_constraints = _planning_constraints(constraints, prompt_policy)

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

        path, diagnostics = shortest_path(network, context.state["position"], goal, planning_constraints)
        full_path, full_diagnostics = shortest_path(network, network.get("start", context.state["position"]), goal, planning_constraints)
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
        route_segments = summarize_route_segments(network, full_path or path)
        route_advice = route_advice_text(route_segments, style=prompt_policy.get("agent_b_response_style", "compact"))
        constraints_changed = constraints and constraints != belief_before.get("constraints", [])
        if context.shared_state.get("route_advice") and constraints_changed:
            text = f"Route fits: {_constraint_phrase(constraints)}."
            dialogue_act = "constraint_response"
            intent = "evaluate_secondary_constraints"
        elif context.shared_state.get("route_advice") and prompt_policy.get("avoid_repetition", True):
            text = "Continue."
            dialogue_act = "route_followup"
            intent = "execute_agreed_route"
        else:
            text = route_advice
            dialogue_act = "route_proposal"
            intent = "calculate_line_route"
        return AgentResponse(
            text=text,
            interpreted_action=action,
            metadata={
                "dialogue_act": dialogue_act,
                "intent": intent,
                "interpreted_goal": goal,
                "interpreted_constraints": constraints,
                "proposed_action": action,
                "selected_action": action,
                "route_plan": path,
                "route_segments": route_segments,
                "route_advice": route_advice,
                "route_diagnostics": {**diagnostics, "full_route": full_diagnostics, "planning_constraints": planning_constraints},
                "constraint_satisfied": True,
                "belief_state_before": belief_before,
                "belief_state_after": belief_after,
                "ambiguity_detected": False,
                "repair_or_clarification": False,
            },
        )


def _resolve_goal(text: str, network: dict[str, Any]) -> list[int] | None:
    lowered = text.lower()
    stations = network.get("stations") or network.get("landmarks", {})
    for label, position in stations.items():
        label_text = label.lower()
        if f"get off at {label_text}" in lowered or f"to {label_text}" in lowered or f"destination {label_text}" in lowered:
            return list(position)
    mentions = [
        (lowered.rfind(label.lower()), position)
        for label, position in stations.items()
        if label.lower() in lowered
    ]
    if mentions:
        return list(max(mentions, key=lambda item: item[0])[1])
    destination_match = re.search(r"(?:get off at|to|destination)\s*\[(\d+),\s*(\d+)\]", lowered)
    if destination_match:
        return [int(destination_match.group(1)), int(destination_match.group(2))]
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
    if "full" in lowered or "crowd" in lowered:
        constraints.append("low_fullness")
    if "transfer" in lowered or "transition" in lowered or "change" in lowered:
        constraints.append("few_transfers")
    return constraints


def _planning_constraints(constraints: list[str], prompt_policy: dict[str, Any]) -> list[str]:
    values = list(constraints)
    if prompt_policy.get("route_strategy", "shortest_path_first") == "shortest_path_first" and "prefer_shortest" not in values:
        values.append("prefer_shortest")
    return values


def _constraint_phrase(constraints: list[str]) -> str:
    labels = {
        "avoid_blocked": "avoid blocked nodes",
        "prefer_shortest": "short route",
        "low_fullness": "low fullness",
        "few_transfers": "few transfers",
    }
    readable = [labels.get(item, item.replace("_", " ")) for item in constraints]
    if not readable:
        return "the stated constraints"
    if len(readable) == 1:
        return readable[0]
    return ", ".join(readable[:-1]) + f" and {readable[-1]}"


def _goal_label(goal: list[int], network: dict[str, Any]) -> str:
    for label, position in (network.get("stations") or network.get("landmarks", {})).items():
        if list(position) == list(goal):
            return label
    return str(goal)
