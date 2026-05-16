from __future__ import annotations

from typing import Any


def analyze_run(transcript: dict[str, Any]) -> dict[str, Any]:
    metrics = transcript.get("metrics", {})
    failure_category = _failure_category(transcript, metrics)
    return {
        "failure_category": failure_category,
        "failure_explanation": _failure_explanation(failure_category),
        "key_events": _key_events(transcript),
        "route_summary": transcript.get("route_summary", {}),
        "cooperation_summary": _cooperation_summary(transcript),
        "metric_breakdown": _metric_breakdown(transcript),
    }


def _failure_category(transcript: dict[str, Any], metrics: dict[str, Any]) -> str:
    if transcript.get("success") and metrics.get("constraint_violation_count", 0) == 0:
        return "success"
    if metrics.get("goal_mention_turn", -1) < 0:
        return "no_goal_communicated"
    if metrics.get("goal_interpretation_accuracy", 0) < 1:
        return "goal_misinterpreted"
    if metrics.get("constraint_interpretation_accuracy", 0) < 1:
        return "constraint_misinterpreted"
    if any(turn.get("dialogue_act") == "failure_report" for turn in transcript.get("turns", [])):
        return "no_valid_route"
    if metrics.get("invalid_action_count", 0) >= transcript.get("system_profile", {}).get("max_invalid_moves", 3):
        return "invalid_action_loop"
    if metrics.get("clarification_count", 0) > max(2, metrics.get("turn_count", 0) / 2):
        return "excessive_clarification"
    if metrics.get("constraint_violation_count", 0) > 0:
        return "constraint_violation"
    if metrics.get("route_optimality_ratio", 1) < 0.75:
        return "route_suboptimal"
    if not transcript.get("success"):
        return "max_turns_reached"
    return "unknown"


def _failure_explanation(category: str) -> str:
    explanations = {
        "success": "The agents reached the goal without recorded constraint violations.",
        "no_goal_communicated": "Agent A never produced an explicit goal mention.",
        "goal_misinterpreted": "Agent B's final interpreted goal did not match Agent A's private goal.",
        "constraint_misinterpreted": "Agent B's interpreted constraints did not cover Agent A's constraints.",
        "no_valid_route": "Agent B reported that no valid route satisfied the communicated constraints.",
        "invalid_action_loop": "The run stopped after repeated invalid actions.",
        "excessive_clarification": "Clarification dominated the dialogue before the task was solved.",
        "route_suboptimal": "The task succeeded, but the actual path was substantially longer than the optimal route.",
        "constraint_violation": "At least one selected action or route violated a communicated constraint.",
        "max_turns_reached": "The dialogue reached the turn budget before task success.",
        "unknown": "The run failed without matching a more specific diagnostic category.",
    }
    return explanations.get(category, explanations["unknown"])


def _key_events(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    events = []
    for turn in transcript.get("turns", []):
        if turn.get("dialogue_act") in {"goal_request", "clarification_request", "failure_report"} or not turn.get("valid_action", True):
            events.append({
                "turn_id": turn.get("turn_id"),
                "speaker": turn.get("speaker"),
                "dialogue_act": turn.get("dialogue_act"),
                "text": turn.get("text"),
            })
    return events[:10]


def _cooperation_summary(transcript: dict[str, Any]) -> dict[str, Any]:
    shared = transcript.get("shared_dialogue_state", {})
    return {
        "final_shared_goal": shared.get("known_goal"),
        "final_shared_constraints": shared.get("known_constraints", []),
        "unresolved_ambiguities": shared.get("unresolved_ambiguities", 0),
        "agent_a_knows_network": transcript.get("agent_a_private_knowledge", {}).get("knows_network", False),
        "agent_b_knows_network": transcript.get("agent_b_private_knowledge_summary", {}).get("knows_network", False),
    }


def _metric_breakdown(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    from sds_eval.metrics.metric_registry import metric_explanations

    return metric_explanations(transcript)
