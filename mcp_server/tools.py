"""
mcp_server/tools.py

PURPOSE:
This is the MCP (Model Context Protocol) tool layer. Instead of every
agent file directly importing pandas and reading CSVs itself (tight
coupling), all data access goes through these tool functions instead.

WHY THIS MATTERS ARCHITECTURALLY:
In a real production system, you don't want 5 different agents each
independently opening the same CSV file with their own pandas logic —
if the data source ever changes (CSV -> real database -> live API),
you'd have to update every single agent. By centralizing data access
behind a tool interface, only THIS file would need to change.

This module is written using the MCP tool-definition pattern: each
function is a self-contained "tool" with a clear name, description,
and typed inputs/outputs — the same shape real MCP servers use, so
agents can call them uniformly instead of writing raw pandas inline.

NOTE ON SCOPE: This implements the MCP *tool pattern* (clean, typed,
single-purpose data-access functions, callable by name) directly in
Python so every agent in this project — CrewAI, AutoGen, and LangGraph
nodes alike — can call the exact same underlying tools, rather than
each having its own copy of the data-access logic.
"""

import os
import pandas as pd
from datetime import timedelta

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(CURRENT_DIR, "..", "data", "products.csv")
ORDERS_FILE = os.path.join(CURRENT_DIR, "..", "data", "orders.csv")

_products_df = pd.read_csv(PRODUCTS_FILE)
_orders_df = pd.read_csv(ORDERS_FILE)
_orders_df["order_timestamp"] = pd.to_datetime(_orders_df["order_timestamp"])


# ============================================================
# TOOL: get_all_products
# ============================================================
def get_all_products() -> list[dict]:
    """
    MCP Tool: Returns the full product catalog.
    Used by: storefront UI (browse page), Inventory sub-agents.
    """
    return _products_df.to_dict(orient="records")


# ============================================================
# TOOL: search_products
# ============================================================
def search_products(query: str) -> list[dict]:
    """
    MCP Tool: Keyword search over product names.
    Used by: storefront search bar, Inventory Agent.
    """
    query_words = query.lower().split()
    matches = _products_df[
        _products_df["product_name"].str.lower().apply(
            lambda name: any(word in name for word in query_words)
        )
    ]
    return matches.to_dict(orient="records")


# ============================================================
# TOOL: get_low_stock_products
# ============================================================
def get_low_stock_products() -> list[dict]:
    """
    MCP Tool: Returns products at or below their reorder threshold.
    Used by: Inventory sub-agents.
    """
    low = _products_df[_products_df["stock_quantity"] <= _products_df["reorder_threshold"]]
    return low.to_dict(orient="records")


# ============================================================
# TOOL: get_product_by_id
# ============================================================
def get_product_by_id(product_id: str) -> dict | None:
    """
    MCP Tool: Look up a single product by its ID.
    Used by: storefront product detail view, Inventory Agent.
    """
    match = _products_df[_products_df["product_id"] == product_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


# ============================================================
# TOOL: get_order_by_id
# ============================================================
def get_order_by_id(order_id: str) -> dict | None:
    """
    MCP Tool: Look up a single order by its ID.
    Used by: Support sub-agents, Fraud sub-agents.
    """
    match = _orders_df[_orders_df["order_id"].str.upper() == order_id.upper()]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


# ============================================================
# TOOL: get_orders_by_email
# ============================================================
def get_orders_by_email(email: str) -> list[dict]:
    """
    MCP Tool: Returns all orders placed by a given email address.
    Used by: Support Agent — lets customers look up their order history.
    """
    matches = _orders_df[_orders_df["customer_email"].str.lower() == email.lower()]
    if matches.empty:
        return []
    return matches.to_dict(orient="records")


# ============================================================
# TOOL: get_fraud_signals
# ============================================================
def get_fraud_signals(order_id: str) -> dict | None:
    """
    MCP Tool: Runs all rule-based fraud signal checks on one order
    and returns the structured signal results.
    Used by: Fraud sub-agents (Signal Analyst role specifically).
    """
    order = get_order_by_id(order_id)
    if order is None:
        return None

    order_row = _orders_df[_orders_df["order_id"] == order["order_id"]].iloc[0]

    # Signal 1: velocity — same email, multiple orders within 15 min
    same_email = _orders_df[_orders_df["customer_email"] == order_row["customer_email"]]
    window = timedelta(minutes=15)
    nearby = same_email[
        (same_email["order_timestamp"] >= order_row["order_timestamp"] - window)
        & (same_email["order_timestamp"] <= order_row["order_timestamp"] + window)
    ]
    velocity_flag = len(nearby) > 1

    # Signal 2: country mismatch
    country_mismatch = order_row["shipping_country"] != order_row["billing_country"]

    # Signal 3: new account + high value
    new_account_high_value = (
        order_row["customer_account_age_days"] <= 3 and order_row["order_amount"] >= 100
    )

    # Signal 4: disposable email
    disposable_markers = ["tempmail", "guest", "temp", "10minutemail", "throwaway"]
    disposable_email = any(m in order_row["customer_email"].lower() for m in disposable_markers)

    total = sum([velocity_flag, country_mismatch, new_account_high_value, disposable_email])

    return {
        "order_id": order["order_id"],
        "velocity_flag": velocity_flag,
        "velocity_count": len(nearby),
        "country_mismatch": country_mismatch,
        "new_account_high_value": new_account_high_value,
        "disposable_email": disposable_email,
        "total_flags": total,
    }


# ============================================================
# TOOL: get_all_flagged_orders
# ============================================================
def get_all_flagged_orders() -> list[dict]:
    """
    MCP Tool: Scans all orders, returns those with 2+ fraud signals triggered.
    Used by: Fraud sub-agents.
    """
    flagged = []
    for order_id in _orders_df["order_id"]:
        signals = get_fraud_signals(order_id)
        if signals and signals["total_flags"] >= 2:
            flagged.append(signals)
    return flagged


# ============================================================
# TOOL: append_order
# ============================================================
_next_order_num = 2016

def append_order(customer_name: str, customer_email: str, shipping_country: str,
                  product_id: str, quantity: int = 1) -> dict:
    """
    MCP Tool: Appends a new order to the in-memory orders DataFrame.
    Used by: Storefront checkout flow — generates a real order ID so the
    Fraud Agent can immediately analyze a freshly placed order.
    """
    global _next_order_num, _orders_df
    import pandas as pd
    from datetime import datetime

    product = get_product_by_id(product_id)
    if product is None:
        return {"error": f"Product {product_id} not found"}

    order_id = f"O{_next_order_num}"
    _next_order_num += 1

    now = datetime.now()
    new_order = pd.DataFrame([{
        "order_id": order_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "product_id": product_id,
        "quantity": quantity,
        "order_amount": round(product["price"] * quantity, 2),
        "order_timestamp": now,
        "shipping_country": shipping_country,
        "billing_country": shipping_country,
        "payment_method": "Credit Card",
        "customer_account_age_days": 0,
    }])
    _orders_df = pd.concat([_orders_df, new_order], ignore_index=True)
    # Ensure the combined DataFrame has datetime type for timestamps
    _orders_df["order_timestamp"] = pd.to_datetime(_orders_df["order_timestamp"])

    return {
        "order_id": order_id,
        "product_name": product["product_name"],
        "total": round(product["price"] * quantity, 2),
    }


# ============================================================
# TOOL REGISTRY
# ============================================================
# This dict is what lets agents call tools BY NAME (the actual MCP
# pattern) instead of importing functions directly — this is what
# decouples "which agent" from "which tool implementation."
TOOL_REGISTRY = {
    "get_all_products": get_all_products,
    "search_products": search_products,
    "get_low_stock_products": get_low_stock_products,
    "get_product_by_id": get_product_by_id,
    "get_order_by_id": get_order_by_id,
    "get_orders_by_email": get_orders_by_email,
    "get_fraud_signals": get_fraud_signals,
    "get_all_flagged_orders": get_all_flagged_orders,
    "append_order": append_order,
}


def call_tool(tool_name: str, **kwargs):
    """
    The actual MCP-style invocation function — agents call THIS,
    passing a tool name and arguments, rather than calling Python
    functions directly. This is the layer that would change if you
    ever swapped this for a real MCP server over a network protocol.
    """
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOL_REGISTRY[tool_name](**kwargs)
