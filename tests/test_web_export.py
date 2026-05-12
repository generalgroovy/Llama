import json

from sds_eval.analysis.export_web import export_web_data


def test_web_export_generation(tmp_path):
    run = {
        "run_id": "run_1",
        "experiment_id": "exp",
        "seed": 1,
        "config": {"parameters": {}},
        "agent_a": {"name": "UserLM", "metadata": {}},
        "agent_b": {"name": "RuleAgent", "metadata": {}},
        "task": {"map_id": "m", "complexity": "simple"},
        "turns": [],
        "state_trace": [],
        "action_trace": [],
        "final_state": {"distance_to_goal": 0},
        "success": True,
        "errors": [],
        "metrics": {"task_success": 1.0, "turn_count": 2},
    }
    source = tmp_path / "runs.json"
    source.write_text(json.dumps({"experiment": {"experiment_id": "exp"}, "runs": [run]}), encoding="utf-8")
    out = tmp_path / "web"
    summary = export_web_data([source], out)
    assert summary["runs"] == 1
    assert (out / "experiments.json").exists()
    assert (out / "runs.json").exists()
    assert (out / "metrics.json").exists()
    assert (out / "transcripts" / "run_1.json").exists()
