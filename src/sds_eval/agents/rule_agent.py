from __future__ import annotations

from sds_eval.agents.base import AgentAdapter, AgentContext, AgentResponse


class RuleAgent(AgentAdapter):
    """Deterministic SDS agent that maps instruction text to navigation actions."""

    KEYWORDS = {
        "north": ("north", "up"),
        "south": ("south", "down"),
        "east": ("east", "right"),
        "west": ("west", "left"),
        "stay": ("stay", "wait"),
        "clarify": ("clarify", "unclear", "repeat", "closer"),
    }

    def __init__(self, name: str = "RuleAgent", metadata: dict | None = None):
        super().__init__(name, metadata or {"role": "deterministic_sds"})

    def respond(self, context: AgentContext) -> AgentResponse:
        instruction = (context.last_instruction or "").lower()
        action = "clarify"
        for candidate, words in self.KEYWORDS.items():
            if any(word in instruction for word in words):
                action = candidate
                break
        return AgentResponse(text=f"Interpreted action: {action}", interpreted_action=action)
