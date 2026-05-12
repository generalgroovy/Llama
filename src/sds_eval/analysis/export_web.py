from __future__ import annotations

import json
from pathlib import Path

from sds_eval.analysis.reliability import compute_reliability


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
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    experiments, runs = load_run_files(run_paths)
    metrics = {
        "aggregate": _aggregate_metrics(runs),
        "reliability": compute_reliability(runs),
        "run_metrics": [{"run_id": run["run_id"], **run.get("metrics", {})} for run in runs],
    }
    compact_runs = []
    for run in runs:
        transcript_path = transcripts_dir / f"{run['run_id']}.json"
        transcript_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
        compact_runs.append({
            "run_id": run["run_id"],
            "experiment_id": run["experiment_id"],
            "seed": run["seed"],
            "agent_b": run["agent_b"],
            "task": run["task"],
            "success": run["success"],
            "metrics": run["metrics"],
            "transcript_url": f"data/transcripts/{run['run_id']}.json",
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
