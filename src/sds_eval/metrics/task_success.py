from __future__ import annotations


def task_success(transcript: dict) -> float:
    return 1.0 if transcript.get("success") else 0.0


def path_distance_error(transcript: dict) -> int:
    return int(transcript.get("final_state", {}).get("distance_to_goal", 0))
