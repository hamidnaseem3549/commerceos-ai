"""Tests for MCP tool layer."""
from commerceos.mcp.tools import (
    get_all_products,
    get_fraud_signals,
    get_low_stock_products,
    get_order_by_id,
    get_orders_by_email,
    get_product_by_id,
    search_products,
)


def test_get_all_products():
    products = get_all_products()
    assert len(products) > 0
    assert "product_id" in products[0]
    assert "product_name" in products[0]


def test_search_products():
    results = search_products("t-shirt")
    assert len(results) > 0
    names = [p["product_name"].lower() for p in results]
    assert any("t-shirt" in n for n in names)


def test_search_products_no_match():
    results = search_products("zzzznotfoundzzzz")
    assert len(results) == 0


def test_get_order_by_id_found():
    order = get_order_by_id("O2001")
    assert order is not None
    assert order["order_id"] == "O2001"


def test_get_order_by_id_not_found():
    order = get_order_by_id("O9999")
    assert order is None


def test_get_product_by_id():
    product = get_product_by_id("P1001")
    assert product is not None
    assert product["product_name"] == "Classic Cotton T-Shirt - Black"


def test_get_low_stock_products():
    low = get_low_stock_products()
    assert len(low) > 0
    for p in low:
        assert p["stock_quantity"] <= p["reorder_threshold"]


def test_get_fraud_signals():
    signals = get_fraud_signals("O2001")
    assert signals is not None
    assert "total_flags" in signals
    assert "velocity_flag" in signals


def test_get_orders_by_email():
    orders = get_orders_by_email("sarah.ahmed@email.com")
    assert len(orders) > 0
    assert orders[0]["customer_email"] == "sarah.ahmed@email.com"


def test_get_orders_by_email_not_found():
    orders = get_orders_by_email("nonexistent@email.com")
    assert len(orders) == 0
