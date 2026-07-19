"""
agents/support_agent.py

PURPOSE:
Handles customer questions about orders, refunds, and returns.
Uses RAG (ChromaDB) for policy grounding, and the MCP tool layer for
order lookups -- so order data access is shared with Fraud/Inventory
agents instead of duplicated here.
"""

import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from rag.vectorstore_setup import load_vectorstore
from mcp_server.tools import call_tool

load_dotenv()


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_order_id(text: str):
    words = text.replace("#", " ").replace(",", " ").split()
    for word in words:
        if word.upper().startswith("O") and word[1:].isdigit():
            return word.upper()
    return None


def extract_email(text: str):
    """Extract an email address from text if present."""
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def run_support_agent(user_query: str) -> dict:

    vectorstore = load_vectorstore()
    retrieved_docs = vectorstore.similarity_search(user_query, k=3)
    policy_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    order_context = ""
    order_id = extract_order_id(user_query)
    email = extract_email(user_query)

    # Check 1: If an order ID is mentioned, look it up
    if order_id:
        order = call_tool("get_order_by_id", order_id=order_id)
        if order:
            order_context = (
                f"\nOrder Details:\n"
                f"- Order ID: {order['order_id']}\n"
                f"- Customer: {order['customer_name']}\n"
                f"- Email: {order['customer_email']}\n"
                f"- Product ID: {order['product_id']}\n"
                f"- Amount: ${order['order_amount']}\n"
                f"- Quantity: {order['quantity']}\n"
                f"- Order Date: {order['order_timestamp']}\n"
                f"- Shipping to: {order['shipping_country']}\n"
                f"- Status: {'Found in system' if order else 'Not found'}\n"
            )
        else:
            order_context = f"\nOrder ID {order_id} was NOT found in our system. The customer may have the wrong ID.\n"

    # Check 2: If an email is mentioned (and no specific order ID), show order history
    elif email:
        orders = call_tool("get_orders_by_email", email=email)
        if orders:
            lines = [f"\nOrder History for {email}:"]
            for o in sorted(orders, key=lambda x: x["order_timestamp"], reverse=True):
                lines.append(
                    f"- {o['order_id']} | {o['product_id']} | ${o['order_amount']} "
                    f"| {o['order_timestamp']} | Shipping: {o['shipping_country']}"
                )
            order_context = "\n".join(lines)
        else:
            order_context = f"\nNo orders found for email: {email}. The customer may have used a different email.\n"

    system_prompt = (
        "You are a helpful customer support agent for Urban Thread Co., an online clothing and lifestyle store. "
        "You have two sources of knowledge:\n\n"
        "1. GENERAL E-COMMERCE KNOWLEDGE (use your own training for this):\n"
        "   - How to browse products, add to cart, and checkout\n"
        "   - How to place an order (go to Home page → search/browse → Add to Cart → Cart page → Place Order)\n"
        "   - How to check order status (contact support with your order ID)\n"
        "   - Payment methods (Credit Card, Debit Card, PayPal)\n"
        "   - Shipping times (domestic 5-10 business days, international 10-20 business days)\n"
        "   - General store information\n\n"
        "2. STORE POLICY (use the policy sections below for this — be precise, quote policy):\n"
        "   - Refunds, returns, exchanges, damaged items, warranties\n"
        "   - Any specific policy questions\n\n"
        "RULES:\n"
        "- Be concise, professional, and warm\n"
        "- For general how-to questions (buying, ordering, payments), answer naturally from your knowledge\n"
        "- For policy questions (refunds, returns, claims), use ONLY the policy sections below\n"
        "- If neither your knowledge nor the policy covers the question, say so honestly and suggest escalating\n"
    )

    full_prompt = (
        f"{system_prompt}\n\n"
        f"--- POLICY SECTIONS (use ONLY for refund/return/claim questions) ---\n{policy_context}\n"
        f"{order_context}\n"
        f"--- CUSTOMER QUESTION ---\n{user_query}\n\n"
        f"Your response:"
    )

    llm = ChatGroq(model="qwen/qwen3-32b", temperature=0.3)
    response = llm.invoke(full_prompt)

    return {
        "agent": "Customer Support Agent",
        "answer": strip_think_tags(response.content),
        "context_used": policy_context + order_context,
    }


if __name__ == "__main__":
    test_questions = [
        "Where is my order O2001?",
        "Can I get a refund on a damaged item?",
        "I want to return earrings I bought, is that possible?",
        "How do I place an order?",
        "What payment methods do you accept?",
    ]
    for q in test_questions:
        print(f"\nQ: {q}")
        result = run_support_agent(q)
        print(f"A: {result['answer']}")