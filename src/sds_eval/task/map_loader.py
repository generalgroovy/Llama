from __future__ import annotations

from pathlib import Path

import yaml

from sds_eval.task.navigation_env import NavigationMap


def load_maps(path: str | Path) -> dict[str, NavigationMap]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    maps: dict[str, NavigationMap] = {}
    for item in raw.get("maps", []):
        stations = {key: tuple(value) for key, value in item.get("stations", item.get("landmarks", {})).items()}
        nav_map = NavigationMap(
            map_id=item["map_id"],
            width=int(item["width"]),
            height=int(item["height"]),
            start=tuple(item["start"]),
            goal=tuple(item["goal"]),
            landmarks={key: tuple(value) for key, value in item.get("landmarks", {}).items()},
            stations=stations,
            transit_lines=_load_transit_lines(item.get("transit_lines", {}), stations),
            obstacles={tuple(value) for value in item.get("obstacles", [])},
            complexity=item.get("complexity", "simple"),
        )
        maps[nav_map.map_id] = nav_map
    return maps


def _load_transit_lines(raw_lines: dict, stations: dict[str, tuple[int, int]]) -> dict[str, list[tuple[int, int]]]:
    lines: dict[str, list[tuple[int, int]]] = {}
    for line_name, raw_stops in raw_lines.items():
        stops = raw_stops.get("stops", raw_stops) if isinstance(raw_stops, dict) else raw_stops
        parsed = []
        for stop in stops:
            if isinstance(stop, str):
                parsed.append(stations[stop])
            else:
                parsed.append(tuple(stop))
        lines[str(line_name)] = parsed
    return lines
