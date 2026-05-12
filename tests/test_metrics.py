from sds_eval.metrics.metric_registry import compute_all_metrics


def test_metric_computation():
    transcript = {
        "success": True,
        "final_state": {"distance_to_goal": 0},
        "agent_b": {"name": "RuleAgent"},
        "task": {"complexity": "simple"},
        "config": {"parameters": {"language_noise": 0.0, "ambiguity_level": 0.0}},
        "action_trace": [{"valid_action": True}],
        "turns": [
            {"speaker": "UserLM", "text": "go east", "interpreted_action": "east", "repair_or_clarification": False},
            {"speaker": "RuleAgent", "text": "Interpreted action: east", "interpreted_action": "east", "repair_or_clarification": False},
        ],
    }
    metrics = compute_all_metrics(transcript)
    assert metrics["task_success"] == 1.0
    assert metrics["turn_count"] == 2
    assert metrics["semantic_action_consistency"] == 1.0
    assert metrics["invalid_action_count"] == 0
