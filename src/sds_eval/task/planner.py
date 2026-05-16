from __future__ import annotations

from collections import deque
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

    queue: deque[tuple[Position, list[Position]]] = deque([(start_pos, [start_pos])])
    seen = {start_pos}
    expanded = 0
    while queue:
        current, path = queue.popleft()
        expanded += 1
        if current == goal_pos:
            return [_as_list(pos) for pos in path], {
                "planner": "bfs",
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


def _neighbors(pos: Position, width: int, height: int) -> list[Position]:
    values: list[Position] = []
    for action in ("north", "east", "south", "west"):
        dx, dy = ACTION_DELTAS[action]
        nxt = (pos[0] + dx, pos[1] + dy)
        if 0 <= nxt[0] < width and 0 <= nxt[1] < height:
            values.append(nxt)
    return values


def _position(value: list[int] | tuple[int, int]) -> Position:
    return int(value[0]), int(value[1])


def _as_list(value: Position) -> list[int]:
    return [value[0], value[1]]
