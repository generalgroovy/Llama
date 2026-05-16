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
        goal = private.get("goal")
        constraints = list(private.get("constraints", ["avoid_blocked"]))
        ambiguity = float(context.parameters.get("ambiguity_level", 0.0))
        noise = float(context.parameters.get("language_noise", 0.0))

        known_goal = shared.get("b_belief", {}).get("goal")
        if context.state.get("success"):
            text = "Goal reached. Stop."
            dialogue_act = "stop"
            intent = "finish_task"
        elif not known_goal:
            dialogue_act = "goal_request"
            intent = "communicate_goal_and_constraints"
            text = f"Goal: {goal_label}. Constraints: {', '.join(constraints)}. Please plan the next step."
            if ambiguity and self._rng.random() < ambiguity:
                text = "I need to get there while respecting the constraints. Please plan the next step."
        else:
            dialogue_act = "confirmation"
            intent = "continue_shared_plan"
            text = f"Confirmed. Continue toward {goal_label} while respecting {', '.join(constraints)}."
            if ambiguity and self._rng.random() < ambiguity:
                text = "Confirmed. Continue with the agreed plan."
        if noise and self._rng.random() < noise:
            text = f"{text} please maybe"
        mentioned_goal = None if text.lower().startswith("i need") else goal_label
        return AgentResponse(
            text=text,
            interpreted_action=None,
            metadata={
                "dialogue_act": dialogue_act,
                "intent": intent,
                "mentioned_goal": mentioned_goal,
                "mentioned_constraints": constraints if "constraint" in text.lower() or "avoid" in text.lower() else [],
                "private_goal": goal,
                "private_constraints": constraints,
                "uses_network_topology": False,
            },
        )
