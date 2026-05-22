from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field

ACTION_DELTAS = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
    "stay": (0, 0),
}
VALID_ACTIONS = set(ACTION_DELTAS) | {"clarify", "stop"}


@dataclass
class NavigationMap:
    map_id: str
    width: int
    height: int
    start: tuple[int, int]
    goal: tuple[int, int]
    landmarks: dict[str, tuple[int, int]] = field(default_factory=dict)
    stations: dict[str, tuple[int, int]] = field(default_factory=dict)
    transit_lines: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    obstacles: set[tuple[int, int]] = field(default_factory=set)
    complexity: str = "simple"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["start"] = list(self.start)
        data["goal"] = list(self.goal)
        data["landmarks"] = {key: list(value) for key, value in self.landmarks.items()}
        data["stations"] = {key: list(value) for key, value in self.stations.items()}
        data["transit_lines"] = {
            line: [list(value) for value in stops]
            for line, stops in self.transit_lines.items()
        }
        data["obstacles"] = [list(value) for value in sorted(self.obstacles)]
        return data


@dataclass
class StepResult:
    action: str
    state_before: dict
    state_after: dict
    valid_action: bool
    error: str | None = None


class NavigationEnvironment:
    def __init__(self, nav_map: NavigationMap):
        self.map = nav_map
        self.position = nav_map.start
        self.path: list[tuple[int, int]] = [self.position]

    def reset(self) -> dict:
        self.position = self.map.start
        self.path = [self.position]
        return self.state()

    def state(self) -> dict:
        return {
            "map_id": self.map.map_id,
            "position": list(self.position),
            "distance_to_goal": self.distance_to_goal(),
            "success": self.position == self.map.goal,
        }

    def apply_action(self, action: str) -> StepResult:
        before = self.state()
        if action not in VALID_ACTIONS:
            return StepResult(action, before, before, False, f"unknown action: {action}")
        if action in {"clarify", "stop"}:
            return StepResult(action, before, before, True)
        dx, dy = ACTION_DELTAS[action]
        nxt = (self.position[0] + dx, self.position[1] + dy)
        if not self._is_open(nxt):
            return StepResult(action, before, before, False, "blocked or out of bounds")
        self.position = nxt
        self.path.append(nxt)
        return StepResult(action, before, self.state(), True)

    def distance_to_goal(self) -> int:
        if self.position == self.map.goal:
            return 0
        queue = deque([(self.position, 0)])
        seen = {self.position}
        while queue:
            pos, dist = queue.popleft()
            for dx, dy in ACTION_DELTAS.values():
                nxt = (pos[0] + dx, pos[1] + dy)
                if nxt in seen or not self._is_open(nxt):
                    continue
                if nxt == self.map.goal:
                    return dist + 1
                seen.add(nxt)
                queue.append((nxt, dist + 1))
        return self.map.width * self.map.height

    def _is_open(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        return 0 <= x < self.map.width and 0 <= y < self.map.height and pos not in self.map.obstacles
