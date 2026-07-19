"""
agents/inventory_agent.py
Handles stock/inventory questions via MCP tool layer.
Two separate jobs: customer answer + silent background ops alert.
"""

import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_server.tools import call_tool

load_dotenv()


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def run_inventory_agent(user_query: str) -> dict:
    matches = call_tool("search_products", query=user_query)

    if matches:
        product_lines = []
        for p in matches:
            if p["stock_quantity"] == 0:
                status = "OUT OF STOCK"
            elif p["stock_quantity"] <= p["reorder_threshold"]:
                status = f"Only {p['stock_quantity']} left"
            else:
                status = f"In stock ({p['stock_quantity']} units)"
            product_lines.append(
                f"- {p['product_name']} ({p['category']}, ${p['price']}): {status}"
            )
        data_context = "\n".join(product_lines)
        no_matches = False
    else:
        # Search found nothing — note this separately so the agent can respond appropriately
        data_context = f"The customer searched for: '{user_query}'. No matching products found in our catalog."
        no_matches = True

    # If no matches found, agent just says so naturally — no unrelated low-stock dump
    if no_matches:
        customer_prompt = (
            "You are a friendly shop assistant at Urban Thread Co., an online clothing and lifestyle store. "
            "A customer asked about a product we don't seem to carry.\n\n"
            f"Customer asked: {user_query}\n\n"
            "Apologize politely and tell them we don't currently carry that item. "
            "Briefly mention 2-3 product categories we do offer (Apparel, Electronics, Accessories, "
            "Home & Living, Footwear, Sports & Fitness) so they can explore. "
            "Sound natural and helpful, like a real store assistant."
        )
        llm = ChatGroq(model="qwen/qwen3-32b", temperature=0.3)
        customer_answer = strip_think_tags(llm.invoke(customer_prompt).content)
        ops_answer = "NO_ALERT"
        return {
            "agent": "Inventory Agent",
            "answer": customer_answer,
            "ops_alert": "",
            "context_used": data_context,
        }

    # JOB 1: Customer-facing answer — warm, helpful, natural
    customer_prompt = (
        "You are a friendly shop assistant at Urban Thread Co., an online clothing and lifestyle store. "
        "Answer the customer's question warmly and helpfully in 2-4 sentences.\n"
        "RULES:\n"
        "- Tell the customer what's available, out of stock, or running low\n"
        "- If a specific product isn't found, suggest related alternatives from the catalog\n"
        "- Sound like a real helpful sales person in a store, not a robot\n"
        "- NEVER mention: reorder thresholds, product IDs, restocking, internal data, stock quantities as numbers\n"
        "- Use phrases like 'We have...', 'Let me check...', 'How about...', 'You might like...'\n\n"
        f"Stock info: {data_context}\n\n"
        f"Customer asked: {user_query}\n\n"
        f"Your reply to customer:"
    )

    # JOB 2: Background ops alert — only for store manager, never shown to customer
    ops_prompt = (
        "You are an inventory monitoring system. "
        "Check the stock data and write a brief internal alert ONLY if something needs attention.\n"
        "Format: '[PRODUCT NAME]: [issue]'\n"
        "If everything is fine, reply with exactly: NO_ALERT\n\n"
        f"Stock data:\n{data_context}\n\n"
        f"Internal alert:"
    )

    llm = ChatGroq(model="qwen/qwen3-32b", temperature=0.2)
    customer_answer = strip_think_tags(llm.invoke(customer_prompt).content)
    ops_answer = strip_think_tags(llm.invoke(ops_prompt).content)

    return {
        "agent": "Inventory Agent",
        "answer": customer_answer,
        "ops_alert": "" if "NO_ALERT" in ops_answer else ops_answer,
        "context_used": data_context,
    }


if __name__ == "__main__":
    for q in ["Do we have white t-shirt in stock?", "Do you have mens jeans?"]:
        print(f"\nQ: {q}")
        r = run_inventory_agent(q)
        print(f"Customer answer: {r['answer']}")
        print(f"Ops alert: {r['ops_alert']}")