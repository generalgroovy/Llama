from __future__ import annotations

from statistics import mean, variance


def compute_reliability(runs: list[dict]) -> dict:
    metric_names = sorted({key for run in runs for key, value in run.get("metrics", {}).items() if isinstance(value, (int, float))})
    success = [float(run.get("success", False)) for run in runs]
    correlations = {
        metric: _pearson([float(run["metrics"].get(metric, 0.0)) for run in runs], success)
        for metric in metric_names
    }
    variances = {
        metric: _variance([float(run["metrics"].get(metric, 0.0)) for run in runs])
        for metric in metric_names
    }
    return {
        "metric_correlation_with_task_success": correlations,
        "variance_across_seeds": variances,
        "sensitivity_to_map_complexity": _group_success(runs, lambda run: run.get("task", {}).get("complexity", "unknown")),
        "sensitivity_to_noise_ambiguity": _group_success(runs, _noise_key),
        "ranking_stability_across_agent_b": _agent_rankings(runs),
    }


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    denom_x = sum((x - mx) ** 2 for x in xs) ** 0.5
    denom_y = sum((y - my) ** 2 for y in ys) ** 0.5
    return numerator / (denom_x * denom_y) if denom_x and denom_y else 0.0


def _variance(values: list[float]) -> float:
    return variance(values) if len(values) > 1 else 0.0


def _group_success(runs: list[dict], key_fn) -> dict:
    groups: dict[str, list[float]] = {}
    for run in runs:
        groups.setdefault(str(key_fn(run)), []).append(float(run.get("success", False)))
    return {key: mean(values) for key, values in groups.items()}


def _noise_key(run: dict) -> str:
    params = run.get("config", {}).get("parameters", {})
    return f"noise={params.get('language_noise', 0)}|ambiguity={params.get('ambiguity_level', 0)}"


def _agent_rankings(runs: list[dict]) -> list[dict]:
    groups: dict[str, list[float]] = {}
    for run in runs:
        agent = run.get("agent_b", {}).get("name", "unknown")
        groups.setdefault(agent, []).append(float(run.get("success", False)))
    ranking = sorted(((agent, mean(values)) for agent, values in groups.items()), key=lambda item: item[1], reverse=True)
    return [{"agent_b": agent, "mean_task_success": score, "rank": idx + 1} for idx, (agent, score) in enumerate(ranking)]
