from __future__ import annotations

import json
from pathlib import Path

from sds_eval.analysis.reliability import compute_reliability
from sds_eval.metrics.metric_registry import metric_explanations


def load_run_files(paths: list[str | Path]) -> tuple[list[dict], list[dict]]:
    experiments: list[dict] = []
    runs: list[dict] = []
    for path in paths:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if "runs" in raw:
            experiments.append(raw.get("experiment", {"experiment_id": Path(path).stem}))
            runs.extend(raw["runs"])
        else:
            runs.append(raw)
    return experiments, runs


def export_web_data(run_paths: list[str | Path], out_dir: str | Path) -> dict:
    out_dir = Path(out_dir)
    transcripts_dir = out_dir / "transcripts"
    explanations_dir = out_dir / "explanations"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    explanations_dir.mkdir(parents=True, exist_ok=True)
    experiments, runs = load_run_files(run_paths)
    metrics = {
        "aggregate": _aggregate_metrics(runs),
        "reliability": compute_reliability(runs),
        "run_metrics": [{"run_id": run["run_id"], **run.get("metrics", {})} for run in runs],
        "metric_definitions": _metric_definitions(runs),
    }
    compact_runs = []
    for run in runs:
        transcript_path = transcripts_dir / f"{run['run_id']}.json"
        transcript_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
        explanation = run.get("failure_analysis", {})
        (explanations_dir / f"{run['run_id']}.json").write_text(json.dumps(explanation, indent=2), encoding="utf-8")
        compact_runs.append({
            "run_id": run["run_id"],
            "experiment_id": run["experiment_id"],
            "seed": run["seed"],
            "agent_b": run["agent_b"],
            "task": run["task"],
            "success": run["success"],
            "metrics": run["metrics"],
            "system_profile": run.get("system_profile", {}),
            "failure_category": explanation.get("failure_category"),
            "failure_explanation": explanation.get("failure_explanation"),
            "route_summary": run.get("route_summary", {}),
            "transcript_url": f"data/transcripts/{run['run_id']}.json",
            "explanation_url": f"data/explanations/{run['run_id']}.json",
        })
    (out_dir / "experiments.json").write_text(json.dumps(experiments, indent=2), encoding="utf-8")
    (out_dir / "runs.json").write_text(json.dumps(compact_runs, indent=2), encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return {"experiments": len(experiments), "runs": len(runs), "out_dir": str(out_dir)}


def _aggregate_metrics(runs: list[dict]) -> dict:
    if not runs:
        return {}
    numeric: dict[str, list[float]] = {}
    for run in runs:
        for key, value in run.get("metrics", {}).items():
            if isinstance(value, (int, float)):
                numeric.setdefault(key, []).append(float(value))
    return {key: sum(values) / len(values) for key, values in numeric.items()}


def _metric_definitions(runs: list[dict]) -> list[dict]:
    if not runs:
        return []
    seen = set()
    definitions = []
    for item in metric_explanations(runs[0]):
        name = item["metric_name"]
        if name in seen:
            continue
        seen.add(name)
        definitions.append({
            "metric_name": name,
            "definition": item["definition"],
            "interpretation": item["interpretation"],
        })
    return definitions
