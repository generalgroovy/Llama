from __future__ import annotations


def reached_goal(final_state: dict, task: dict) -> bool:
    return list(final_state.get("position", [])) == list(task.get("goal", []))
