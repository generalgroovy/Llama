from __future__ import annotations

REQUIRED_TRANSCRIPT_FIELDS = {
    "run_id",
    "experiment_id",
    "seed",
    "config",
    "agent_a",
    "agent_b",
    "agent_a_private_knowledge",
    "agent_b_private_knowledge_summary",
    "shared_dialogue_state",
    "knowledge_split",
    "system_profile",
    "task",
    "turns",
    "state_trace",
    "action_trace",
    "route_summary",
    "final_state",
    "success",
    "errors",
    "metrics",
    "failure_analysis",
}

REQUIRED_TURN_FIELDS = {
    "turn_id",
    "speaker",
    "text",
    "dialogue_act",
    "intent",
    "mentioned_goal",
    "mentioned_constraints",
    "interpreted_goal",
    "interpreted_constraints",
    "proposed_action",
    "selected_action",
    "interpreted_action",
    "route_plan",
    "state_before",
    "state_after",
    "valid_action",
    "constraint_satisfied",
    "repair_or_clarification",
    "ambiguity_detected",
    "belief_state_before",
    "belief_state_after",
    "errors",
}


def validate_transcript(transcript: dict) -> None:
    missing = REQUIRED_TRANSCRIPT_FIELDS - set(transcript)
    if missing:
        raise ValueError(f"transcript missing fields: {sorted(missing)}")
    for turn in transcript["turns"]:
        turn_missing = REQUIRED_TURN_FIELDS - set(turn)
        if turn_missing:
            raise ValueError(f"turn missing fields: {sorted(turn_missing)}")
