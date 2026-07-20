from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.agents.registry import AgentRegistry
from commerceos.agents.support_agent import SupportAgent
from commerceos.agents.inventory_agent import InventoryAgent
from commerceos.agents.fraud_agent import FraudAgent
from commerceos.agents.order_agent import OrderAgent

AgentRegistry.register(SupportAgent())
AgentRegistry.register(InventoryAgent())
AgentRegistry.register(FraudAgent())
AgentRegistry.register(OrderAgent())

__all__ = ["BaseAgent", "AgentResult", "AgentRegistry"]
