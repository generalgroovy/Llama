from __future__ import annotations

import random

from sds_eval.agents.base import AgentAdapter, AgentContext, AgentResponse
from sds_eval.task.navigation_env import ACTION_DELTAS


ACTION_WORDS = {
    "north": "go north",
    "south": "go south",
    "east": "go east",
    "west": "go west",
    "stay": "stay",
}


class UserLMAgent(AgentAdapter):
    """Synthetic user agent that emits route instructions toward the goal."""

    def __init__(self, name: str = "UserLM", metadata: dict | None = None):
        super().__init__(name, metadata or {"role": "instruction_generator"})
        self._rng = random.Random()

    def reset(self, seed: int | None = None) -> None:
        super().reset(seed)
        self._rng.seed(seed)

    def respond(self, context: AgentContext) -> AgentResponse:
        state = tuple(context.state["position"])
        goal = tuple(context.task["goal"])
        blocked = {tuple(item) for item in context.task.get("obstacles", [])}
        width = context.task["width"]
        height = context.task["height"]
        action = _greedy_valid_action(state, goal, width, height, blocked)
        ambiguity = float(context.parameters.get("ambiguity_level", 0.0))
        noise = float(context.parameters.get("language_noise", 0.0))
        text = ACTION_WORDS.get(action, "stay")
        if ambiguity and self._rng.random() < ambiguity:
            text = "move closer to the target landmark"
        if noise and self._rng.random() < noise:
            text = f"{text} please maybe"
        return AgentResponse(text=text, interpreted_action=action, metadata={"intended_action": action})


def _greedy_valid_action(
    state: tuple[int, int],
    goal: tuple[int, int],
    width: int,
    height: int,
    blocked: set[tuple[int, int]],
) -> str:
    sx, sy = state
    gx, gy = goal
    candidates: list[str] = []
    if gx > sx:
        candidates.append("east")
    if gx < sx:
        candidates.append("west")
    if gy > sy:
        candidates.append("south")
    if gy < sy:
        candidates.append("north")
    candidates.extend(["north", "east", "south", "west"])
    for action in candidates:
        dx, dy = ACTION_DELTAS[action]
        nxt = (sx + dx, sy + dy)
        if 0 <= nxt[0] < width and 0 <= nxt[1] < height and nxt not in blocked:
            return action
    return "stay"
