from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.agents.registry import AgentRegistry
from commerceos.agents.support_agent import SupportAgent
from commerceos.agents.inventory_agent import InventoryAgent
from commerceos.agents.fraud_agent import FraudAgent

AgentRegistry.register(SupportAgent())
AgentRegistry.register(InventoryAgent())
AgentRegistry.register(FraudAgent())

__all__ = ["BaseAgent", "AgentResult", "AgentRegistry"]
