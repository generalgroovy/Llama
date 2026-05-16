from sds_eval.agents.base import AgentContext
from sds_eval.agents.rule_agent import RuleAgent
from sds_eval.agents.userlm import UserLMAgent
from sds_eval.metrics.metric_registry import compute_all_metrics
from sds_eval.task.planner import next_action_for_path, shortest_path


def test_agent_a_does_not_require_network_topology():
    context = AgentContext(
        experiment_id="exp",
        run_id="run",
        turn_id=0,
        state={"position": [0, 0], "success": False},
        private_context={"goal": [2, 0], "goal_label": "library", "constraints": ["avoid_blocked"], "knows_network": False},
        shared_state={"b_belief": {}},
        parameters={},
    )
    response = UserLMAgent().respond(context)
    assert response.interpreted_action is None
    assert response.metadata["uses_network_topology"] is False
    assert "network" not in context.private_context


def test_agent_b_plans_from_private_network_and_updates_belief():
    network = {
        "map_id": "m",
        "width": 3,
        "height": 2,
        "start": [0, 0],
        "goal": [2, 0],
        "landmarks": {"library": [2, 0]},
        "obstacles": [[1, 0]],
    }
    context = AgentContext(
        experiment_id="exp",
        run_id="run",
        turn_id=1,
        state={"position": [0, 0], "success": False},
        last_instruction="Goal: library. Constraints: avoid_blocked. Please plan the next step.",
        private_context={"network": network},
        shared_state={"b_belief": {}},
    )
    response = RuleAgent().respond(context)
    assert response.interpreted_action == "south"
    assert response.metadata["belief_state_after"]["goal"] == [2, 0]
    assert "avoid_blocked" in response.metadata["belief_state_after"]["constraints"]


def test_shortest_path_and_action_selection():
    network = {"width": 3, "height": 2, "obstacles": [[1, 0]]}
    path, diagnostics = shortest_path(network, [0, 0], [2, 0], ["avoid_blocked"])
    assert diagnostics["path_found"]
    assert path == [[0, 0], [0, 1], [1, 1], [2, 1], [2, 0]]
    assert next_action_for_path(path) == "south"


def test_route_optimality_metric():
    transcript = {
        "success": True,
        "final_state": {"distance_to_goal": 0},
        "route_summary": {"shortest_path_length": 4, "actual_path_length": 5},
        "agent_a_private_knowledge": {"constraints": ["avoid_blocked"], "goal": [2, 0]},
        "shared_dialogue_state": {"known_goal": [2, 0], "known_constraints": ["avoid_blocked"]},
        "agent_a": {"name": "UserLM"},
        "agent_b": {"name": "RuleAgent"},
        "turns": [],
        "action_trace": [],
        "task": {"complexity": "simple"},
        "config": {"parameters": {}},
    }
    metrics = compute_all_metrics(transcript)
    assert metrics["route_optimality_ratio"] == 0.8
