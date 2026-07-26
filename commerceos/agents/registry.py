"""AgentRegistry — agents register here, supervisor routes from here."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from commerceos.agents.base import BaseAgent


class AgentRegistry:
    _agents: dict[str, BaseAgent] = {}  # noqa: RUF012

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        cls._agents[agent.name] = agent

    @classmethod
    def get(cls, name: str) -> BaseAgent | None:
        return cls._agents.get(name)

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._agents.keys())

    @classmethod
    def route(cls, query: str) -> str | None:
        """Route query to the best agent by keyword matching."""
        query_lower = query.lower()
        best_match = None
        best_len = 0
        for name, agent in cls._agents.items():
            for kw in agent.keywords:
                if kw in query_lower and len(kw) > best_len:
                    best_match = name
                    best_len = len(kw)
        return best_match
