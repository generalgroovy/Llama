from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DialogueState:
    turn_id: int = 0
    invalid_moves: int = 0
    errors: list[str] = field(default_factory=list)
