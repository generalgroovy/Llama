from sds_eval.agents.base import AgentContext
from sds_eval.agents.rule_agent import RuleAgent
from sds_eval.agents.userlm import UserLMAgent
from sds_eval.metrics.metric_registry import compute_all_metrics
from sds_eval.task.planner import next_action_for_path, route_advice_text, shortest_path, summarize_route_segments


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


def test_path_is_compressed_into_line_segments():
    network = {
        "width": 4,
        "height": 4,
        "stations": {"Alpha": [0, 0], "Bravo": [3, 0], "Harbor": [3, 3]},
        "transit_lines": {
            "R": [[0, 0], [1, 0], [2, 0], [3, 0]],
            "EW2": [[3, 0], [3, 1], [3, 2], [3, 3]],
        },
        "obstacles": [],
    }
    path, _ = shortest_path(network, [0, 0], [3, 3], ["prefer_shortest"])
    segments = summarize_route_segments(network, path)
    assert segments == [
        {"line": "R", "from_station": "Alpha", "to_station": "Bravo", "from_position": [0, 0], "to_position": [3, 0], "steps": 3},
        {"line": "EW2", "from_station": "Bravo", "to_station": "Harbor", "from_position": [3, 0], "to_position": [3, 3], "steps": 3},
    ]
    assert route_advice_text(segments) == "Take R: Alpha -> Bravo; EW2: Bravo -> Harbor."


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


def test_agents_avoid_repeating_route_details_after_first_advice():
    network = {
        "map_id": "m",
        "width": 2,
        "height": 1,
        "start": [0, 0],
        "goal": [1, 0],
        "stations": {"Alpha": [0, 0], "Bravo": [1, 0]},
        "transit_lines": {"R": [[0, 0], [1, 0]]},
        "obstacles": [],
    }
    first = RuleAgent().respond(AgentContext(
        experiment_id="exp",
        run_id="run",
        turn_id=1,
        state={"position": [0, 0], "success": False},
        last_instruction="Route request: get on at Alpha and get off at Bravo. Constraints: prefer_shortest.",
        private_context={"network": network},
        shared_state={"b_belief": {}},
        parameters={"prompt_policy": {"avoid_repetition": True, "agent_b_response_style": "compact"}},
    ))
    second = RuleAgent().respond(AgentContext(
        experiment_id="exp",
        run_id="run",
        turn_id=3,
        state={"position": [0, 0], "success": False},
        last_instruction="Proceed.",
        private_context={"network": network},
        shared_state={"b_belief": first.metadata["belief_state_after"], "route_advice": first.metadata["route_advice"]},
        parameters={"prompt_policy": {"avoid_repetition": True, "agent_b_response_style": "compact"}},
    ))
    assert first.text == "Take R: Alpha -> Bravo."
    assert second.text == "Continue."
