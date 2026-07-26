"""Tests for the LangGraph supervisor end-to-end."""
from commerceos.orchestration.supervisor import handle_query


def test_supervisor_handles_empty_query():
    result = handle_query("")
    assert result["agent_name"] == "System"
    assert "type a question" in result["answer"].lower()


def test_supervisor_handles_whitespace_query():
    result = handle_query("   ")
    assert result["agent_name"] == "System"


def test_supervisor_handles_support_query():
    result = handle_query("What is your return policy?")
    assert result["agent_name"] != "System"


def test_supervisor_handles_order_query():
    result = handle_query("Track my order O2001")
    assert result["route"] == "order"


def test_supervisor_handles_inventory_query():
    result = handle_query("Check stock for t-shirt")
    assert result["route"] == "inventory"


def test_supervisor_returns_route_and_answer():
    result = handle_query("Where is my order O2001?", thread_id="test-thread-1")
    assert "route" in result
    assert "answer" in result
    assert len(result["answer"]) > 0


def test_supervisor_preserves_history():
    thread = "test-history-thread"
    handle_query("Hello", thread_id=thread)
    result = handle_query("Is my order shipped?", thread_id=thread)
    assert "history" in result
    assert len(result["history"]) > 0


def test_supervisor_different_threads_independent():
    r1 = handle_query("Check stock", thread_id="thread-a")
    r2 = handle_query("Check fraud", thread_id="thread-b")
    # Different threads should not interfere
    assert r1["route"] in ["inventory", "support"]
    assert r2["route"] in ["fraud", "support"]
