from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from sds_eval.metrics.efficiency import invalid_action_count, token_count, turn_count
from sds_eval.metrics.repair_counts import clarification_count, repair_count
from sds_eval.metrics.semantic_consistency import contradiction_count, semantic_action_consistency
from sds_eval.metrics.task_success import path_distance_error, task_success
from sds_eval.task.planner import route_optimality_ratio

MetricFn = Callable[[dict[str, Any]], Any]


def goal_mention_turn(transcript: dict[str, Any]) -> int:
    for turn in transcript.get("turns", []):
        if turn.get("mentioned_goal"):
            return int(turn["turn_id"])
    return -1


def constraint_mention_count(transcript: dict[str, Any]) -> int:
    return sum(len(turn.get("mentioned_constraints", [])) for turn in transcript.get("turns", []))


def constraint_coverage(transcript: dict[str, Any]) -> float:
    expected = set(transcript.get("agent_a_private_knowledge", {}).get("constraints", []))
    if not expected:
        return 1.0
    mentioned = {item for turn in transcript.get("turns", []) for item in turn.get("mentioned_constraints", [])}
    return len(expected & mentioned) / len(expected)


def ambiguity_rate(transcript: dict[str, Any]) -> float:
    turns = transcript.get("turns", [])
    if not turns:
        return 0.0
    return sum(1 for turn in turns if turn.get("ambiguity_detected")) / len(turns)


def instruction_specificity(transcript: dict[str, Any]) -> float:
    a_turns = [turn for turn in transcript.get("turns", []) if turn.get("speaker") == transcript.get("agent_a", {}).get("name")]
    if not a_turns:
        return 0.0
    scored = 0
    for turn in a_turns:
        if turn.get("mentioned_goal"):
            scored += 1
        if turn.get("mentioned_constraints"):
            scored += 1
    return scored / (2 * len(a_turns))


def correction_count(transcript: dict[str, Any]) -> int:
    return sum(1 for turn in transcript.get("turns", []) if turn.get("dialogue_act") == "correction")


def confirmation_count(transcript: dict[str, Any]) -> int:
    return sum(1 for turn in transcript.get("turns", []) if turn.get("dialogue_act") == "confirmation")


def goal_interpretation_accuracy(transcript: dict[str, Any]) -> float:
    expected = transcript.get("agent_a_private_knowledge", {}).get("goal")
    interpreted = transcript.get("shared_dialogue_state", {}).get("known_goal")
    return 1.0 if expected and interpreted and list(expected) == list(interpreted) else 0.0


def constraint_interpretation_accuracy(transcript: dict[str, Any]) -> float:
    expected = set(transcript.get("agent_a_private_knowledge", {}).get("constraints", []))
    interpreted = set(transcript.get("shared_dialogue_state", {}).get("known_constraints", []))
    if not expected:
        return 1.0
    return len(expected & interpreted) / len(expected)


def intent_classification_accuracy(transcript: dict[str, Any]) -> float:
    classified = [turn for turn in transcript.get("turns", []) if turn.get("intent")]
    return len(classified) / len(transcript.get("turns", []) or [1])


def clarification_precision(transcript: dict[str, Any]) -> float:
    clarification_turns = [turn for turn in transcript.get("turns", []) if turn.get("dialogue_act") == "clarification_request"]
    if not clarification_turns:
        return 1.0
    useful = [turn for turn in clarification_turns if turn.get("ambiguity_detected")]
    return len(useful) / len(clarification_turns)


def clarification_recall(transcript: dict[str, Any]) -> float:
    ambiguous = [turn for turn in transcript.get("turns", []) if turn.get("ambiguity_detected")]
    if not ambiguous:
        return 1.0
    requested = [turn for turn in ambiguous if turn.get("dialogue_act") == "clarification_request"]
    return len(requested) / len(ambiguous)


def belief_update_accuracy(transcript: dict[str, Any]) -> float:
    return (goal_interpretation_accuracy(transcript) + constraint_interpretation_accuracy(transcript)) / 2


def shared_goal_alignment(transcript: dict[str, Any]) -> float:
    return goal_interpretation_accuracy(transcript)


def shared_constraint_alignment(transcript: dict[str, Any]) -> float:
    return constraint_interpretation_accuracy(transcript)


def plan_agreement_rate(transcript: dict[str, Any]) -> float:
    b_turns = [turn for turn in transcript.get("turns", []) if turn.get("speaker") == transcript.get("agent_b", {}).get("name")]
    if not b_turns:
        return 0.0
    agreed = [turn for turn in b_turns if turn.get("route_plan") and turn.get("valid_action")]
    return len(agreed) / len(b_turns)


def clarification_resolution_rate(transcript: dict[str, Any]) -> float:
    if clarification_count(transcript) == 0:
        return 1.0
    return 1.0 if transcript.get("shared_dialogue_state", {}).get("known_goal") else 0.0


def repair_success_rate(transcript: dict[str, Any]) -> float:
    repairs = repair_count(transcript)
    if repairs == 0:
        return 1.0
    return 1.0 if transcript.get("success") else 0.0


def unnecessary_turn_count(transcript: dict[str, Any]) -> int:
    return sum(1 for turn in transcript.get("turns", []) if turn.get("dialogue_act") == "confirmation" and transcript.get("shared_dialogue_state", {}).get("known_goal"))


def cooperation_efficiency(transcript: dict[str, Any]) -> float:
    turns = max(1, turn_count(transcript))
    return task_success(transcript) * plan_agreement_rate(transcript) / turns


def belief_state_delta_score(transcript: dict[str, Any]) -> float:
    initial = {}
    final = transcript.get("shared_dialogue_state", {}).get("b_belief", {})
    return float(len(set(final) - set(initial)))


def shortest_path_length(transcript: dict[str, Any]) -> int:
    return int(transcript.get("route_summary", {}).get("shortest_path_length", 0))


def actual_path_length(transcript: dict[str, Any]) -> int:
    return int(transcript.get("route_summary", {}).get("actual_path_length", 0))


def route_optimality(transcript: dict[str, Any]) -> float:
    return route_optimality_ratio(actual_path_length(transcript), shortest_path_length(transcript), bool(transcript.get("success")))


def blocked_action_attempts(transcript: dict[str, Any]) -> int:
    return sum(1 for action in transcript.get("action_trace", []) if action.get("error") == "blocked or out of bounds")


def backtracking_count(transcript: dict[str, Any]) -> int:
    positions = [tuple(state.get("position", [])) for state in transcript.get("state_trace", [])]
    return sum(1 for idx in range(2, len(positions)) if positions[idx] == positions[idx - 2])


def stay_action_count(transcript: dict[str, Any]) -> int:
    return sum(1 for action in transcript.get("action_trace", []) if action.get("action") == "stay")


def constraint_violation_count(transcript: dict[str, Any]) -> int:
    return sum(1 for turn in transcript.get("turns", []) if not turn.get("constraint_satisfied", True))


def final_distance_to_goal(transcript: dict[str, Any]) -> int:
    return path_distance_error(transcript)


def action_turn_count(transcript: dict[str, Any]) -> int:
    return sum(1 for turn in transcript.get("turns", []) if turn.get("selected_action"))


def non_action_turn_count(transcript: dict[str, Any]) -> int:
    return max(0, turn_count(transcript) - action_turn_count(transcript))


def repeated_message_count(transcript: dict[str, Any]) -> int:
    counts = Counter(turn.get("text", "") for turn in transcript.get("turns", []))
    return sum(count - 1 for count in counts.values() if count > 1)


def dialogue_act_distribution(transcript: dict[str, Any]) -> dict[str, int]:
    return dict(Counter(turn.get("dialogue_act", "unknown") for turn in transcript.get("turns", [])))


def average_message_length(transcript: dict[str, Any]) -> float:
    turns = transcript.get("turns", [])
    if not turns:
        return 0.0
    return token_count(transcript) / len(turns)


def lexical_noise_level(transcript: dict[str, Any]) -> float:
    tokens = max(1, token_count(transcript))
    noise_markers = sum(turn.get("text", "").lower().count("maybe") for turn in transcript.get("turns", []))
    return noise_markers / tokens


def explicit_reference_count(transcript: dict[str, Any]) -> int:
    return sum(1 for turn in transcript.get("turns", []) if turn.get("mentioned_goal") or turn.get("interpreted_goal"))


def unresolved_reference_count(transcript: dict[str, Any]) -> int:
    return 1 if not transcript.get("shared_dialogue_state", {}).get("known_goal") else 0


def naturalness_proxy_score(transcript: dict[str, Any]) -> float:
    avg = average_message_length(transcript)
    if avg <= 0:
        return 0.0
    length_score = 1.0 if 3 <= avg <= 18 else 0.5
    contradiction_penalty = min(0.5, contradiction_count(transcript) * 0.1)
    noise_penalty = min(0.3, lexical_noise_level(transcript))
    return max(0.0, length_score - contradiction_penalty - noise_penalty)


def audio_recording_count(transcript: dict[str, Any]) -> int:
    return len(transcript.get("audio_recordings", []))


def tts_audio_coverage(transcript: dict[str, Any]) -> float:
    tts_enabled = transcript.get("speech_pipeline", {}).get("tts", {}).get("enabled", False)
    if not tts_enabled:
        return 1.0
    turns = max(1, turn_count(transcript))
    return audio_recording_count(transcript) / turns


def mean_asr_confidence(transcript: dict[str, Any]) -> float:
    return _mean_phase_payload(transcript, "asr", "confidence", default=1.0)


def mean_nlu_confidence(transcript: dict[str, Any]) -> float:
    return _mean_phase_payload(transcript, "nlu", "confidence", default=1.0)


def mean_pipeline_latency_ms(transcript: dict[str, Any]) -> float:
    latencies = [event.get("latency_ms", 0.0) for turn in transcript.get("turns", []) for event in turn.get("pipeline_events", [])]
    return sum(latencies) / len(latencies) if latencies else 0.0


def pipeline_phase_count(transcript: dict[str, Any]) -> int:
    return sum(len(turn.get("pipeline_events", [])) for turn in transcript.get("turns", []))


def asr_enabled(transcript: dict[str, Any]) -> float:
    return 1.0 if transcript.get("speech_pipeline", {}).get("asr", {}).get("enabled", False) else 0.0


def tts_enabled(transcript: dict[str, Any]) -> float:
    return 1.0 if transcript.get("speech_pipeline", {}).get("tts", {}).get("enabled", False) else 0.0


def _mean_phase_payload(transcript: dict[str, Any], phase: str, key: str, default: float) -> float:
    values = [
        float(event.get("payload", {}).get(key, default))
        for turn in transcript.get("turns", [])
        for event in turn.get("pipeline_events", [])
        if event.get("phase") == phase
    ]
    return sum(values) / len(values) if values else default


def robustness_by_condition(transcript: dict[str, Any]) -> dict[str, Any]:
    params = transcript.get("config", {}).get("parameters", {})
    return {
        "condition": {
            "ambiguity_level": params.get("ambiguity_level", 0),
            "language_noise": params.get("language_noise", 0),
            "agent_b": params.get("agent_b", transcript.get("agent_b", {}).get("name")),
            "map_complexity": transcript.get("task", {}).get("complexity"),
            "system_profile": transcript.get("system_profile", {}).get("name", "low"),
        },
        "success": task_success(transcript),
        "distance_error": path_distance_error(transcript),
    }


METRICS: dict[str, MetricFn] = {
    "task_success": task_success,
    "path_distance_error": path_distance_error,
    "turn_count": turn_count,
    "token_count": token_count,
    "repair_count": repair_count,
    "clarification_count": clarification_count,
    "contradiction_count": contradiction_count,
    "semantic_action_consistency": semantic_action_consistency,
    "invalid_action_count": invalid_action_count,
    "goal_mention_turn": goal_mention_turn,
    "constraint_mention_count": constraint_mention_count,
    "constraint_coverage": constraint_coverage,
    "ambiguity_rate": ambiguity_rate,
    "instruction_specificity": instruction_specificity,
    "correction_count": correction_count,
    "confirmation_count": confirmation_count,
    "goal_interpretation_accuracy": goal_interpretation_accuracy,
    "constraint_interpretation_accuracy": constraint_interpretation_accuracy,
    "intent_classification_accuracy": intent_classification_accuracy,
    "clarification_precision": clarification_precision,
    "clarification_recall": clarification_recall,
    "belief_update_accuracy": belief_update_accuracy,
    "shared_goal_alignment": shared_goal_alignment,
    "shared_constraint_alignment": shared_constraint_alignment,
    "plan_agreement_rate": plan_agreement_rate,
    "clarification_resolution_rate": clarification_resolution_rate,
    "repair_success_rate": repair_success_rate,
    "unnecessary_turn_count": unnecessary_turn_count,
    "cooperation_efficiency": cooperation_efficiency,
    "belief_state_delta_score": belief_state_delta_score,
    "shortest_path_length": shortest_path_length,
    "actual_path_length": actual_path_length,
    "route_optimality_ratio": route_optimality,
    "blocked_action_attempts": blocked_action_attempts,
    "backtracking_count": backtracking_count,
    "stay_action_count": stay_action_count,
    "constraint_violation_count": constraint_violation_count,
    "final_distance_to_goal": final_distance_to_goal,
    "action_turn_count": action_turn_count,
    "non_action_turn_count": non_action_turn_count,
    "repeated_message_count": repeated_message_count,
    "dialogue_act_distribution": dialogue_act_distribution,
    "average_message_length": average_message_length,
    "lexical_noise_level": lexical_noise_level,
    "explicit_reference_count": explicit_reference_count,
    "unresolved_reference_count": unresolved_reference_count,
    "naturalness_proxy_score": naturalness_proxy_score,
    "audio_recording_count": audio_recording_count,
    "tts_audio_coverage": tts_audio_coverage,
    "mean_asr_confidence": mean_asr_confidence,
    "mean_nlu_confidence": mean_nlu_confidence,
    "mean_pipeline_latency_ms": mean_pipeline_latency_ms,
    "pipeline_phase_count": pipeline_phase_count,
    "asr_enabled": asr_enabled,
    "tts_enabled": tts_enabled,
    "robustness_by_condition": robustness_by_condition,
}

METRIC_DEFINITIONS: dict[str, str] = {
    "task_success": "1 when the final navigation state reaches the goal, otherwise 0.",
    "route_optimality_ratio": "Shortest valid path length divided by actual path length for successful runs.",
    "goal_interpretation_accuracy": "1 when Agent B's final believed goal matches Agent A's private goal.",
    "constraint_interpretation_accuracy": "Share of Agent A constraints present in Agent B's final belief.",
    "cooperation_efficiency": "Task success and plan agreement normalized by dialogue length.",
    "tts_audio_coverage": "Share of turns with a generated audio recording when TTS is enabled.",
    "mean_asr_confidence": "Average ASR confidence reported by turn-level ASR phase events.",
    "mean_nlu_confidence": "Average NLU confidence reported by turn-level NLU phase events.",
    "mean_pipeline_latency_ms": "Average measured latency across logged pipeline phase events.",
}


def compute_all_metrics(transcript: dict[str, Any]) -> dict[str, Any]:
    return {name: fn(transcript) for name, fn in METRICS.items()}


def metric_explanations(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = transcript.get("metrics") or compute_all_metrics(transcript)
    explanations = []
    for name, value in metrics.items():
        if isinstance(value, dict):
            continue
        explanations.append({
            "metric_name": name,
            "value": value,
            "definition": METRIC_DEFINITIONS.get(name, f"Computed from transcript field evidence for {name}."),
            "numerator": _numerator(name, transcript),
            "denominator": _denominator(name, transcript),
            "interpretation": _interpretation(name, value),
            "related_run_ids": [transcript.get("run_id")],
            "warning": "sample size is one run" if transcript.get("run_id") else None,
        })
    return explanations


def _numerator(name: str, transcript: dict[str, Any]) -> Any:
    if name == "constraint_interpretation_accuracy":
        expected = set(transcript.get("agent_a_private_knowledge", {}).get("constraints", []))
        interpreted = set(transcript.get("shared_dialogue_state", {}).get("known_constraints", []))
        return len(expected & interpreted)
    if name == "route_optimality_ratio":
        return shortest_path_length(transcript)
    return None


def _denominator(name: str, transcript: dict[str, Any]) -> Any:
    if name == "constraint_interpretation_accuracy":
        return len(transcript.get("agent_a_private_knowledge", {}).get("constraints", []))
    if name == "route_optimality_ratio":
        return actual_path_length(transcript)
    return None


def _interpretation(name: str, value: Any) -> str:
    if isinstance(value, (int, float)):
        if name.endswith("accuracy") or name.endswith("ratio") or name.endswith("rate") or name.endswith("score"):
            return "higher is better"
        if "count" in name or "error" in name or "violation" in name:
            return "lower is better"
    return "descriptive"
