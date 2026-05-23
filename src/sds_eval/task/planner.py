from __future__ import annotations

from collections import deque
from heapq import heappop, heappush
from typing import Any

from sds_eval.task.navigation_env import ACTION_DELTAS

Position = tuple[int, int]


def shortest_path(
    network: dict[str, Any],
    start: list[int] | tuple[int, int],
    goal: list[int] | tuple[int, int],
    constraints: list[str] | None = None,
) -> tuple[list[list[int]], dict[str, Any]]:
    """Return the shortest valid position path for a grid-derived network."""

    constraints = constraints or []
    start_pos = _position(start)
    goal_pos = _position(goal)
    obstacles = {_position(item) for item in network.get("obstacles", [])}
    width = int(network["width"])
    height = int(network["height"])

    if "prefer_shortest" in constraints:
        return _optimized_shortest_path(network, start_pos, goal_pos, width, height, obstacles, constraints)

    queue: deque[tuple[Position, list[Position]]] = deque([(start_pos, [start_pos])])
    seen = {start_pos}
    expanded = 0
    while queue:
        current, path = queue.popleft()
        expanded += 1
        if current == goal_pos:
            return [_as_list(pos) for pos in path], {
                "planner": "bfs",
                "optimization_strategy": "shortest_path",
                "expanded_nodes": expanded,
                "path_found": True,
                "constraints": constraints,
            }
        for nxt in _neighbors(current, width, height):
            if nxt in seen or nxt in obstacles:
                continue
            seen.add(nxt)
            queue.append((nxt, [*path, nxt]))
    return [], {
        "planner": "bfs",
        "optimization_strategy": "shortest_path",
        "expanded_nodes": expanded,
        "path_found": False,
        "constraints": constraints,
    }


def next_action_for_path(path: list[list[int]]) -> str:
    if len(path) < 2:
        return "stay"
    current = _position(path[0])
    nxt = _position(path[1])
    dx = nxt[0] - current[0]
    dy = nxt[1] - current[1]
    for action, delta in ACTION_DELTAS.items():
        if delta == (dx, dy):
            return action
    return "stay"


def path_length(path: list[list[int]]) -> int:
    return max(0, len(path) - 1)


def route_optimality_ratio(actual_steps: int, shortest_steps: int, success: bool) -> float:
    if not success or actual_steps <= 0:
        return 0.0
    if shortest_steps <= 0:
        return 1.0
    return min(1.0, shortest_steps / actual_steps)


def summarize_route_segments(network: dict[str, Any], path: list[list[int]]) -> list[dict[str, Any]]:
    """Compress a node path into line-based advice segments."""

    if len(path) < 2:
        return []
    segments: list[dict[str, Any]] = []
    current_line: str | None = None
    segment_start = path[0]
    previous_position = path[0]
    for idx in range(1, len(path)):
        current_position = path[idx]
        line = _line_for_edge(network, previous_position, current_position, current_line)
        if current_line is None:
            current_line = line
        elif line != current_line:
            segments.append(_segment(network, current_line, segment_start, previous_position))
            segment_start = previous_position
            current_line = line
        previous_position = current_position
    if current_line is not None:
        segments.append(_segment(network, current_line, segment_start, path[-1]))
    return segments


def route_advice_text(segments: list[dict[str, Any]], style: str = "compact") -> str:
    if not segments:
        return "No valid line route is available."
    if style == "compact":
        parts = [
            f"{segment['line']}: {segment['from_station']} -> {segment['to_station']}"
            for segment in segments
        ]
        return "Take " + "; ".join(parts) + "."
    parts = [
        f"take line {segment['line']} from {segment['from_station']} to {segment['to_station']}"
        for segment in segments
    ]
    if len(parts) == 1:
        return _sentence_case(parts[0]) + "."
    return f"{_sentence_case(parts[0])}, then " + ", then ".join(parts[1:]) + "."


def _neighbors(pos: Position, width: int, height: int) -> list[Position]:
    values: list[Position] = []
    for action in ("north", "east", "south", "west"):
        dx, dy = ACTION_DELTAS[action]
        nxt = (pos[0] + dx, pos[1] + dy)
        if 0 <= nxt[0] < width and 0 <= nxt[1] < height:
            values.append(nxt)
    return values


def _optimized_shortest_path(
    network: dict[str, Any],
    start_pos: Position,
    goal_pos: Position,
    width: int,
    height: int,
    obstacles: set[Position],
    constraints: list[str],
) -> tuple[list[list[int]], dict[str, Any]]:
    heap: list[tuple[int, int, int, int, Position, str | None, list[Position]]] = []
    push_order = 0
    heappush(heap, (0, 0, 0, push_order, start_pos, None, [start_pos]))
    best: dict[tuple[Position, str | None], tuple[int, int, int]] = {(start_pos, None): (0, 0, 0)}
    expanded = 0
    while heap:
        steps, walk_edges, transfers, order, current, current_line, path = heappop(heap)
        expanded += 1
        if current == goal_pos:
            return [_as_list(pos) for pos in path], {
                "planner": "dijkstra",
                "optimization_strategy": "shortest_path_first",
                "primary_objective": "minimize_number_of_edges",
                "secondary_objective": "prefer_transit_line_edges_over_walk_edges",
                "tertiary_objective": "minimize_transfers_for_equal_length_paths",
                "expanded_nodes": expanded,
                "path_found": True,
                "path_length": steps,
                "walk_edges": walk_edges,
                "transfers": transfers,
                "constraints": constraints,
            }
        for nxt in _neighbors(current, width, height):
            if nxt in obstacles:
                continue
            for line in _candidate_lines_for_edge(network, _as_list(current), _as_list(nxt)) or ["walk"]:
                next_walk_edges = walk_edges + (1 if line == "walk" else 0)
                next_transfers = transfers + (1 if current_line and line != current_line else 0)
                next_steps = steps + 1
                key = (nxt, line)
                cost = (next_steps, next_walk_edges, next_transfers)
                if cost >= best.get(key, (10**9, 10**9, 10**9)):
                    continue
                best[key] = cost
                push_order += 1
                heappush(heap, (next_steps, next_walk_edges, next_transfers, push_order, nxt, line, [*path, nxt]))
    return [], {
        "planner": "dijkstra",
        "optimization_strategy": "shortest_path_first",
        "primary_objective": "minimize_number_of_edges",
        "secondary_objective": "prefer_transit_line_edges_over_walk_edges",
        "tertiary_objective": "minimize_transfers_for_equal_length_paths",
        "expanded_nodes": expanded,
        "path_found": False,
        "constraints": constraints,
    }


def _position(value: list[int] | tuple[int, int]) -> Position:
    return int(value[0]), int(value[1])


def _as_list(value: Position) -> list[int]:
    return [value[0], value[1]]


def _line_for_edge(network: dict[str, Any], a: list[int], b: list[int], previous_line: str | None) -> str:
    candidates = _candidate_lines_for_edge(network, a, b)
    if previous_line in candidates:
        return previous_line
    return sorted(candidates)[0] if candidates else "walk"


def _candidate_lines_for_edge(network: dict[str, Any], a: list[int], b: list[int]) -> list[str]:
    candidates = []
    edge = {_position(a), _position(b)}
    for line_name, stops in network.get("transit_lines", {}).items():
        parsed = [_position(stop) for stop in stops]
        for idx in range(1, len(parsed)):
            if {parsed[idx - 1], parsed[idx]} == edge:
                candidates.append(str(line_name))
                break
    return sorted(candidates)


def _segment(network: dict[str, Any], line: str, start: list[int], end: list[int]) -> dict[str, Any]:
    return {
        "line": line,
        "from_station": station_label(network, start),
        "to_station": station_label(network, end),
        "from_position": start,
        "to_position": end,
        "steps": abs(end[0] - start[0]) + abs(end[1] - start[1]),
    }


def station_label(network: dict[str, Any], position: list[int] | tuple[int, int]) -> str:
    pos = list(position)
    stations = network.get("stations") or network.get("landmarks", {})
    for label, station_position in stations.items():
        if list(station_position) == pos:
            return str(label)
    return f"[{pos[0]}, {pos[1]}]"


def _sentence_case(value: str) -> str:
    return value[:1].upper() + value[1:]
