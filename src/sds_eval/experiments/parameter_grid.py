from __future__ import annotations

from itertools import product


def expand_grid(grid: dict) -> list[dict]:
    if not grid:
        return [{}]
    keys = list(grid)
    values = [value if isinstance(value, list) else [value] for value in grid.values()]
    return [dict(zip(keys, combo, strict=True)) for combo in product(*values)]
