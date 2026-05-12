from __future__ import annotations

import os

from sds_eval.agents.base import AgentAdapter, AgentContext, AgentResponse
from sds_eval.agents.rule_agent import RuleAgent


class ChatGPTAgent(AgentAdapter):
    """Placeholder adapter for a future live LLM-backed SDS agent.

    No API call is made here so experiments remain reproducible in local and CI
    runs. Future integration can read OPENAI_API_KEY and replace the fallback.
    """

    def __init__(self, name: str = "ChatGPTAgent", metadata: dict | None = None):
        super().__init__(name, metadata or {"role": "llm_sds_placeholder", "live_api": False})
        self._fallback = RuleAgent(name="RuleFallback")

    def reset(self, seed: int | None = None) -> None:
        super().reset(seed)
        self._fallback.reset(seed)

    def respond(self, context: AgentContext) -> AgentResponse:
        if os.getenv("OPENAI_API_KEY"):
            # TODO: integrate the OpenAI Responses API behind an explicit config flag.
            pass
        response = self._fallback.respond(context)
        response.metadata["placeholder"] = "ChatGPTAgent currently uses deterministic fallback"
        return response
