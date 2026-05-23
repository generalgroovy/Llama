from __future__ import annotations

REQUIRED_TRANSCRIPT_FIELDS = {
    "run_id",
    "experiment_id",
    "seed",
    "config",
    "speech_pipeline",
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
    "audio_recordings",
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
    "spoken_text",
    "recognized_text",
    "dialogue_act",
    "intent",
    "mentioned_goal",
    "mentioned_origin",
    "mentioned_start_time",
    "mentioned_constraints",
    "interpreted_goal",
    "interpreted_constraints",
    "proposed_action",
    "selected_action",
    "interpreted_action",
    "route_plan",
    "route_segments",
    "route_advice",
    "pipeline_events",
    "audio_path",
    "audio_sidecar_path",
    "audio_duration_seconds",
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
