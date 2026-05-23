from __future__ import annotations

import random

from sds_eval.agents.base import AgentAdapter, AgentContext, AgentResponse


class UserLMAgent(AgentAdapter):
    """Synthetic user agent that communicates goals and constraints only."""

    def __init__(self, name: str = "UserLM", metadata: dict | None = None):
        super().__init__(name, metadata or {"role": "instruction_generator"})
        self._rng = random.Random()

    def reset(self, seed: int | None = None) -> None:
        super().reset(seed)
        self._rng.seed(seed)

    def respond(self, context: AgentContext) -> AgentResponse:
        private = context.private_context
        shared = context.shared_state
        goal_label = private.get("goal_label", "goal")
        origin_label = private.get("origin_label", "start")
        goal = private.get("goal")
        constraints = list(private.get("constraints", ["avoid_blocked"]))
        prompt_policy = context.parameters.get("prompt_policy", {})
        avoid_repetition = bool(prompt_policy.get("avoid_repetition", True))
        ambiguity = float(context.parameters.get("ambiguity_level", 0.0))
        noise = float(context.parameters.get("language_noise", 0.0))

        known_goal = shared.get("b_belief", {}).get("goal")
        known_route = shared.get("route_advice")
        if context.state.get("success"):
            text = "Goal reached. Stop."
            dialogue_act = "stop"
            intent = "finish_task"
            mentioned_goal = None
            mentioned_origin = None
            mentioned_constraints: list[str] = []
        elif not known_goal:
            dialogue_act = "goal_request"
            intent = "communicate_goal_and_constraints"
            text = f"Route request: get on at {origin_label} and get off at {goal_label}. Constraints: {', '.join(constraints)}. Which line should I take?"
            if ambiguity and self._rng.random() < ambiguity:
                text = "I need a line route between my stations while respecting the constraints."
            mentioned_goal = None if text.lower().startswith("i need") else goal_label
            mentioned_origin = origin_label if mentioned_goal else None
            mentioned_constraints = constraints if "constraint" in text.lower() or "avoid" in text.lower() else []
        else:
            dialogue_act = "confirmation"
            intent = "continue_shared_plan"
            if avoid_repetition and known_route:
                text = "Proceed."
                mentioned_goal = None
                mentioned_origin = None
                mentioned_constraints = []
            else:
                text = "Please continue the agreed route."
                mentioned_goal = None
                mentioned_origin = None
                mentioned_constraints = []
            if ambiguity and self._rng.random() < ambiguity:
                text = "Continue."
        if noise and self._rng.random() < noise:
            text = f"{text} please maybe"
        return AgentResponse(
            text=text,
            interpreted_action=None,
            metadata={
                "dialogue_act": dialogue_act,
                "intent": intent,
                "mentioned_goal": mentioned_goal,
                "mentioned_origin": mentioned_origin,
                "mentioned_constraints": mentioned_constraints,
                "route_request": {"from_station": origin_label, "to_station": goal_label},
                "private_goal": goal,
                "private_constraints": constraints,
                "uses_network_topology": False,
            },
        )
