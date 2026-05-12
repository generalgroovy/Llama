from __future__ import annotations


def repair_count(transcript: dict) -> int:
    return sum(1 for turn in transcript.get("turns", []) if turn.get("repair_or_clarification"))


def clarification_count(transcript: dict) -> int:
    return sum(1 for turn in transcript.get("turns", []) if turn.get("interpreted_action") == "clarify")
