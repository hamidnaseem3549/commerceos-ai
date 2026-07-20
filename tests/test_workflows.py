"""Integration tests for event-driven workflows."""
from commerceos.agents import AgentRegistry
from commerceos.orchestration.event_bus import EventBus
from commerceos.mcp.tools import append_order, get_order_by_id


def test_event_bus_integration():
    bus = EventBus()
    events = []

    bus.on("order.created", lambda d: events.append(("fraud_check", d)))
    bus.on("order.created", lambda d: events.append(("inventory_deduct", d)))

    bus.emit("order.created", {"order_id": "O2001", "customer_email": "test@test.com"})

    assert len(events) == 2
    assert events[0][0] == "fraud_check"
    assert events[1][0] == "inventory_deduct"


def test_append_order_creates_order():
    result = append_order(
        customer_name="Test User",
        customer_email="test@example.com",
        shipping_country="USA",
        product_id="P1001",
        quantity=2,
    )
    assert "order_id" in result
    assert result["product_name"] == "Classic Cotton T-Shirt - Black"
    assert result["total"] == 29.98

    order = get_order_by_id(result["order_id"])
    assert order is not None
    assert order["status"] in ["pending", "confirmed"]


def test_supervisor_routing_keywords():
    assert AgentRegistry.route("Where is my order O2001?") == "order"
    assert AgentRegistry.route("Do you have white t-shirt?") == "inventory"
    assert AgentRegistry.route("Can I return damaged item?") == "support"
    assert AgentRegistry.route("Check O2004 for fraud") == "fraud"
    assert AgentRegistry.route("Any items on sale?") == "pricing"
