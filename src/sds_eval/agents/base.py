from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    experiment_id: str
    run_id: str
    turn_id: int
    state: dict[str, Any]
    task: dict[str, Any]
    history: list[dict[str, Any]] = field(default_factory=list)
    last_instruction: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    text: str
    interpreted_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentAdapter(ABC):
    """Common interface for UserLM, rule-based, and external SDS agents."""

    def __init__(self, name: str, metadata: dict[str, Any] | None = None):
        self.name = name
        self.metadata = metadata or {}

    def reset(self, seed: int | None = None) -> None:
        self.metadata["seed"] = seed

    @abstractmethod
    def respond(self, context: AgentContext) -> AgentResponse:
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "metadata": dict(self.metadata)}
