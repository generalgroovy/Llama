from sds_eval.agents import ChatGPTAgent, RuleAgent, UserLMAgent
from sds_eval.agents.base import AgentContext, AgentResponse


def _context(text=None):
    return AgentContext(
        experiment_id="e",
        run_id="r",
        turn_id=0,
        state={"position": [0, 0]},
        task={"width": 3, "height": 3, "goal": [1, 0], "obstacles": []},
        last_instruction=text,
    )


def test_agents_share_adapter_shape():
    for agent in [UserLMAgent(), RuleAgent(), ChatGPTAgent()]:
        agent.reset(7)
        response = agent.respond(_context("go east"))
        assert isinstance(response, AgentResponse)
        assert agent.describe()["name"]


def test_rule_agent_interprets_instruction():
    response = RuleAgent().respond(_context("please go east"))
    assert response.interpreted_action == "east"
