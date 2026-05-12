from __future__ import annotations

REQUIRED_TRANSCRIPT_FIELDS = {
    "run_id",
    "experiment_id",
    "seed",
    "config",
    "agent_a",
    "agent_b",
    "task",
    "turns",
    "state_trace",
    "action_trace",
    "final_state",
    "success",
    "errors",
    "metrics",
}

REQUIRED_TURN_FIELDS = {
    "turn_id",
    "speaker",
    "text",
    "interpreted_action",
    "state_before",
    "state_after",
    "valid_action",
    "repair_or_clarification",
}


def validate_transcript(transcript: dict) -> None:
    missing = REQUIRED_TRANSCRIPT_FIELDS - set(transcript)
    if missing:
        raise ValueError(f"transcript missing fields: {sorted(missing)}")
    for turn in transcript["turns"]:
        turn_missing = REQUIRED_TURN_FIELDS - set(turn)
        if turn_missing:
            raise ValueError(f"turn missing fields: {sorted(turn_missing)}")
