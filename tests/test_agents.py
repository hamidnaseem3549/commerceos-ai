"""Tests for agent registration and routing."""
from commerceos.agents import AgentRegistry


def test_all_agents_registered():
    agents = AgentRegistry.list()
    assert "support" in agents
    assert "inventory" in agents
    assert "fraud" in agents
    assert "order" in agents
    assert "pricing" in agents


def test_support_agent_keywords():
    agent = AgentRegistry.get("support")
    assert agent is not None
    assert "refund" in agent.keywords
    assert "order" in agent.keywords


def test_inventory_agent_keywords():
    agent = AgentRegistry.get("inventory")
    assert agent is not None
    assert "stock" in agent.keywords


def test_fraud_agent_keywords():
    agent = AgentRegistry.get("fraud")
    assert agent is not None
    assert "fraud" in agent.keywords


def test_order_agent_keywords():
    agent = AgentRegistry.get("order")
    assert agent is not None
    assert "track my order" in agent.keywords


def test_pricing_agent_keywords():
    agent = AgentRegistry.get("pricing")
    assert agent is not None
    assert "sale" in agent.keywords


def test_agent_routing():
    assert AgentRegistry.route("where is my order O2001") == "order"
    assert AgentRegistry.route("check stock for t-shirt") == "inventory"
    assert AgentRegistry.route("refund policy for damaged items") == "support"
    assert AgentRegistry.route("any deals today") == "pricing"
    assert AgentRegistry.route("check O2004 for fraud") == "fraud"
