from sds_eval.agents.base import AgentAdapter, AgentContext, AgentResponse
from sds_eval.agents.chatgpt_agent import ChatGPTAgent
from sds_eval.agents.rule_agent import RuleAgent
from sds_eval.agents.userlm import UserLMAgent

AGENT_TYPES = {
    "userlm": UserLMAgent,
    "rule": RuleAgent,
    "rule_agent": RuleAgent,
    "chatgpt": ChatGPTAgent,
    "chatgpt_agent": ChatGPTAgent,
}

__all__ = [
    "AGENT_TYPES",
    "AgentAdapter",
    "AgentContext",
    "AgentResponse",
    "ChatGPTAgent",
    "RuleAgent",
    "UserLMAgent",
]
