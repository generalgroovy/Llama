from __future__ import annotations

ACTION_TERMS = {
    "north": ("north", "up"),
    "south": ("south", "down"),
    "east": ("east", "right"),
    "west": ("west", "left"),
    "stay": ("stay", "wait"),
}

OPPOSITES = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}


def semantic_action_consistency(transcript: dict) -> float:
    checked = 0
    consistent = 0
    turns = transcript.get("turns", [])
    for idx, turn in enumerate(turns):
        action = turn.get("interpreted_action")
        if turn.get("speaker") == transcript.get("agent_b", {}).get("name") and action in ACTION_TERMS and idx > 0:
            checked += 1
            previous_text = turns[idx - 1].get("text", "").lower()
            if any(term in previous_text for term in ACTION_TERMS[action]):
                consistent += 1
    return consistent / checked if checked else 1.0


def contradiction_count(transcript: dict) -> int:
    count = 0
    turns = transcript.get("turns", [])
    for idx, turn in enumerate(turns):
        action = turn.get("interpreted_action")
        if idx == 0 or action not in OPPOSITES:
            continue
        previous_text = turns[idx - 1].get("text", "").lower()
        opposite = OPPOSITES[action]
        if any(term in previous_text for term in ACTION_TERMS[opposite]):
            count += 1
    return count
