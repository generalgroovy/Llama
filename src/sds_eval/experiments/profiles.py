from __future__ import annotations

from copy import deepcopy
from typing import Any

SYSTEM_PROFILES: dict[str, dict[str, Any]] = {
    "low": {
        "name": "low",
        "max_turns": 16,
        "max_invalid_moves": 3,
        "planner": "bfs",
        "metric_detail": "standard",
        "store_full_belief_trace": True,
        "bootstrap_reliability": False,
        "notes": "Default profile for low-end systems; deterministic, small memory footprint, no expensive resampling.",
    },
    "high": {
        "name": "high",
        "max_turns": 40,
        "max_invalid_moves": 5,
        "planner": "bfs",
        "metric_detail": "extended",
        "store_full_belief_trace": True,
        "bootstrap_reliability": True,
        "bootstrap_samples": 200,
        "notes": "Higher-detail profile for larger local or CI systems.",
    },
}


def resolve_system_profile(name: str | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = deepcopy(SYSTEM_PROFILES.get((name or "low").lower(), SYSTEM_PROFILES["low"]))
    for key, value in (overrides or {}).items():
        if value is not None:
            profile[key] = value
    return profile
