from __future__ import annotations


def turn_count(transcript: dict) -> int:
    return len(transcript.get("turns", []))


def token_count(transcript: dict) -> int:
    return sum(len(turn.get("text", "").split()) for turn in transcript.get("turns", []))


def invalid_action_count(transcript: dict) -> int:
    return sum(1 for item in transcript.get("action_trace", []) if not item.get("valid_action", True))
