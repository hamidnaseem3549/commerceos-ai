"""Integration tests for event-driven workflows."""
from commerceos.agents import AgentRegistry
from commerceos.mcp.tools import append_order, get_order_by_id
from commerceos.orchestration.event_bus import EventBus


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


def test_append_order_with_new_customer():
    """New customers should be auto-created."""
    result = append_order(
        customer_name="New Customer",
        customer_email="new.customer@test.com",
        shipping_country="UK",
        product_id="P1002",
        quantity=1,
    )
    assert "order_id" in result
    assert result["product_name"] == "Classic Cotton T-Shirt - White"


def test_append_order_nonexistent_product():
    result = append_order(
        customer_name="Test User",
        customer_email="test@test.com",
        shipping_country="USA",
        product_id="P9999",
        quantity=1,
    )
    assert "error" in result
    assert "P9999" in result["error"]


def test_event_bus_clear_removes_handlers():
    bus = EventBus()
    calls = []

    def handler(data):
        calls.append(data)

    bus.on("test.event", handler)
    assert len(bus._listeners["test.event"]) == 1

    bus.clear()
    assert len(bus._listeners) == 0


def test_event_bus_emit_no_handlers_does_not_crash():
    bus = EventBus()
    # Should not raise
    bus.emit("nonexistent.event", {"data": 1})


def test_event_bus_handler_error_does_not_crash():
    bus = EventBus()

    def failing_handler(data):
        raise ValueError("Intentional test error")

    bus.on("error.event", failing_handler)
    # Should not raise — logs the error and continues
    bus.emit("error.event", {"data": 1})
