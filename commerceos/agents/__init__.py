from commerceos.agents.base import AgentResult, BaseAgent
from commerceos.agents.fraud_agent import FraudAgent
from commerceos.agents.inventory_agent import InventoryAgent
from commerceos.agents.order_agent import OrderAgent
from commerceos.agents.pricing_agent import PricingAgent
from commerceos.agents.registry import AgentRegistry
from commerceos.agents.support_agent import SupportAgent

AgentRegistry.register(SupportAgent())
AgentRegistry.register(InventoryAgent())
AgentRegistry.register(FraudAgent())
AgentRegistry.register(OrderAgent())
AgentRegistry.register(PricingAgent())

__all__ = ["AgentRegistry", "AgentResult", "BaseAgent"]

from commerceos.orchestration.workflows import register_event_handlers

register_event_handlers()
