from __future__ import annotations

from sds_eval.metrics.efficiency import invalid_action_count, token_count, turn_count
from sds_eval.metrics.repair_counts import clarification_count, repair_count
from sds_eval.metrics.semantic_consistency import contradiction_count, semantic_action_consistency
from sds_eval.metrics.task_success import path_distance_error, task_success


def robustness_by_condition(transcript: dict) -> dict:
    params = transcript.get("config", {}).get("parameters", {})
    return {
        "condition": {
            "ambiguity_level": params.get("ambiguity_level", 0),
            "language_noise": params.get("language_noise", 0),
            "agent_b": params.get("agent_b", transcript.get("agent_b", {}).get("name")),
            "map_complexity": transcript.get("task", {}).get("complexity"),
        },
        "success": task_success(transcript),
        "distance_error": path_distance_error(transcript),
    }


METRICS = {
    "task_success": task_success,
    "path_distance_error": path_distance_error,
    "turn_count": turn_count,
    "token_count": token_count,
    "repair_count": repair_count,
    "clarification_count": clarification_count,
    "contradiction_count": contradiction_count,
    "semantic_action_consistency": semantic_action_consistency,
    "invalid_action_count": invalid_action_count,
    "robustness_by_condition": robustness_by_condition,
}


def compute_all_metrics(transcript: dict) -> dict:
    return {name: fn(transcript) for name, fn in METRICS.items()}
