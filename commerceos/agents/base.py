"""Abstract base class for all agents."""
from abc import ABC, abstractmethod
from typing import TypedDict


class AgentResult(TypedDict):
    answer: str
    agent: str
    ops_alert: str
    context_used: str
    actions: list[dict]


class BaseAgent(ABC):
    name: str = ""
    description: str = ""
    keywords: list[str] = []

    @abstractmethod
    def run(self, query: str) -> AgentResult:
        ...
