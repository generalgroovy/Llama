from __future__ import annotations

from pathlib import Path

import yaml

from sds_eval.task.navigation_env import NavigationMap


def load_maps(path: str | Path) -> dict[str, NavigationMap]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    maps: dict[str, NavigationMap] = {}
    for item in raw.get("maps", []):
        nav_map = NavigationMap(
            map_id=item["map_id"],
            width=int(item["width"]),
            height=int(item["height"]),
            start=tuple(item["start"]),
            goal=tuple(item["goal"]),
            landmarks={key: tuple(value) for key, value in item.get("landmarks", {}).items()},
            obstacles={tuple(value) for value in item.get("obstacles", [])},
            complexity=item.get("complexity", "simple"),
        )
        maps[nav_map.map_id] = nav_map
    return maps
