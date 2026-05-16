from __future__ import annotations

import json
from pathlib import Path

import yaml

from sds_eval.agents import AGENT_TYPES, UserLMAgent
from sds_eval.dialogue.manager import DialogueManager
from sds_eval.experiments.parameter_grid import expand_grid
from sds_eval.experiments.profiles import resolve_system_profile
from sds_eval.experiments.seed_control import set_seed
from sds_eval.task.map_loader import load_maps
from sds_eval.task.navigation_env import NavigationEnvironment


def run_experiment(config_path: str | Path) -> dict:
    config_path = Path(config_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = config_path.parents[2] if len(config_path.parents) >= 3 else Path(".")
    maps_path = root / config.get("maps_path", "configs/tasks/navigation_maps.yaml")
    maps = load_maps(maps_path)
    experiment_id = config["experiment_id"]
    system_profile = resolve_system_profile(config.get("system_profile", "low"), config.get("system_profile_overrides", {}))
    runs = []
    for index, params in enumerate(expand_grid(config.get("parameter_grid", {}))):
        seed = int(params.get("seed", config.get("seed", 0)))
        set_seed(seed)
        selected_maps = _select_maps(maps, params)
        for nav_map in selected_maps:
            agent_b_type = str(params.get("agent_b", config.get("agent_b", "rule"))).lower()
            agent_b_cls = AGENT_TYPES.get(agent_b_type, AGENT_TYPES["rule"])
            run_id = f"{experiment_id}_{index:03d}_{nav_map.map_id}_s{seed}"
            run_config = {
                "source_config": str(config_path),
                "parameters": params,
                "system_profile": system_profile["name"],
                "system_profile_overrides": config.get("system_profile_overrides", {}),
                "knowledge_split": config.get("knowledge_split", _default_knowledge_split()),
                "max_turns": config.get("max_turns", system_profile["max_turns"]),
                "max_invalid_moves": config.get("max_invalid_moves", system_profile["max_invalid_moves"]),
            }
            manager = DialogueManager(
                agent_a=UserLMAgent(),
                agent_b=agent_b_cls(),
                environment=NavigationEnvironment(nav_map),
                experiment_id=experiment_id,
                run_id=run_id,
                seed=seed,
                config=run_config,
                max_turns=int(config.get("max_turns", system_profile["max_turns"])),
                max_invalid_moves=int(config.get("max_invalid_moves", system_profile["max_invalid_moves"])),
            )
            runs.append(manager.run())
    return {
        "experiment": {
            "experiment_id": experiment_id,
            "name": config.get("name", experiment_id),
            "description": config.get("description", ""),
            "config": config,
        },
        "runs": runs,
    }


def write_experiment_result(result: dict, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def _select_maps(maps: dict, params: dict) -> list:
    if "map_id" in params:
        return [maps[params["map_id"]]]
    complexity = params.get("map_complexity")
    if complexity:
        selected = [nav_map for nav_map in maps.values() if nav_map.complexity == complexity]
        return selected or list(maps.values())
    return list(maps.values())


def _default_knowledge_split() -> dict:
    return {
        "agent_a": {"knows_goal": True, "knows_constraints": True, "knows_network": False},
        "agent_b": {"knows_goal_initially": False, "knows_constraints_initially": False, "knows_network": True},
    }
