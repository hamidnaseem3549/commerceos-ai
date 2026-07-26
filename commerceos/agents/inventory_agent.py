"""Inventory agent — stock queries + auto-alerts."""
import re

from langchain_groq import ChatGroq

from commerceos.agents.base import AgentResult, BaseAgent
from commerceos.config import settings
from commerceos.mcp.tools import call_tool


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class InventoryAgent(BaseAgent):
    name = "inventory"
    description = "Handles stock and product availability questions"
    keywords = ["stock", "inventory", "available", "restock", "quantity",  # noqa: RUF012
                "in stock", "out of stock", "how many", "do we have",
                "do you have", "is there", "low stock"]

    def run(self, query: str) -> AgentResult:
        matches = call_tool("search_products", query=query)
        actions = [{"agent": "inventory", "action": "query", "detail": f"Searched: {query}"}]

        if matches:
            product_lines = []
            for p in matches:
                if p.get("stock_quantity", 0) == 0:
                    status = "OUT OF STOCK"
                elif p.get("stock_quantity", 0) <= p.get("reorder_threshold", 0):
                    status = f"Only {p['stock_quantity']} left (low stock)"
                else:
                    status = f"In stock ({p['stock_quantity']} units)"
                product_lines.append(f"- {p['product_name']} ({p['category']}, ${p['price']}): {status}")
            data_context = "\n".join(product_lines)
            no_matches = False
        else:
            data_context = f"No matching products found for: '{query}'"
            no_matches = True

        if no_matches:
            prompt = (
                f"You are a friendly shop assistant at {settings.store_name}. "
                f"A customer asked about something we don't carry: '{query}'. "
                f"Apologize and suggest browsing our categories."
            )
            llm = ChatGroq(model=settings.llm_model, temperature=settings.llm_temperature)
            answer = strip_think_tags(llm.invoke(prompt).content)
            return AgentResult(answer=answer, agent="Inventory Agent", ops_alert="",
                               context_used=data_context, actions=actions)

        customer_prompt = (
            f"You are a friendly shop assistant at {settings.store_name}. "
            f"Answer the customer warmly in 2-4 sentences. "
            f"NEVER mention reorder thresholds or stock quantities as numbers. "
            f"Stock info: {data_context}\n\nCustomer asked: {query}\n\nReply:"
        )
        ops_prompt = (
            f"Check stock data and write a brief internal alert ONLY if something needs attention. "
            f"Format: '[PRODUCT]: [issue]'\nIf fine, reply: NO_ALERT\n\n{data_context}"
        )

        llm = ChatGroq(model=settings.llm_model, temperature=settings.llm_temperature)
        answer = strip_think_tags(llm.invoke(customer_prompt).content)
        ops_answer = strip_think_tags(llm.invoke(ops_prompt).content)

        ops_alert = "" if "NO_ALERT" in ops_answer else ops_answer
        if ops_alert:
            actions.append({"agent": "inventory", "action": "alert", "detail": ops_alert})

        return AgentResult(answer=answer, agent="Inventory Agent", ops_alert=ops_alert,
                           context_used=data_context, actions=actions)
