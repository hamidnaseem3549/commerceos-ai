"""Customer support agent — RAG + order lookups."""
import re
from langchain_groq import ChatGroq
from commerceos.config import settings
from commerceos.agents.base import BaseAgent, AgentResult
from rag.vectorstore_setup import load_vectorstore
from commerceos.mcp.tools import call_tool


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_order_id(text: str):
    words = text.replace("#", " ").replace(",", " ").split()
    for word in words:
        if word.upper().startswith("O") and word[1:].isdigit():
            return word.upper()
    return None


def extract_email(text: str):
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


class SupportAgent(BaseAgent):
    name = "support"
    description = "Handles customer questions about orders, refunds, and returns"
    keywords = ["order", "refund", "return", "shipping", "cancel", "damaged", "policy",
                "where is my", "track", "delivery", "exchange", "warranty"]

    def run(self, query: str) -> AgentResult:
        vectorstore = load_vectorstore()
        retrieved_docs = vectorstore.similarity_search(query, k=3)
        policy_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        order_context = ""
        order_id = extract_order_id(query)
        email = extract_email(query)

        if order_id:
            order = call_tool("get_order_by_id", order_id=order_id)
            if order:
                order_context = (
                    f"\nOrder Details:\n"
                    f"- Order ID: {order.get('order_id', '')}\n"
                    f"- Customer: {order.get('customer_name', '')}\n"
                    f"- Email: {order.get('customer_email', '')}\n"
                    f"- Amount: ${order.get('order_amount', 0)}\n"
                    f"- Status: {order.get('status', 'Found in system')}\n"
                )
            else:
                order_context = f"\nOrder ID {order_id} was NOT found in our system.\n"

        system_prompt = (
            "You are a helpful customer support agent for Urban Thread Co. "
            "Be concise, professional, and warm. Use policy info for refund/return questions."
        )
        full_prompt = f"{system_prompt}\n\n--- POLICY ---\n{policy_context}\n{order_context}\n--- QUESTION ---\n{query}\n\nAnswer:"

        llm = ChatGroq(model=settings.llm_model, temperature=settings.llm_temperature)
        response = llm.invoke(full_prompt)

        return AgentResult(
            answer=strip_think_tags(response.content),
            agent="Customer Support Agent",
            ops_alert="",
            context_used=policy_context + order_context,
            actions=[{"agent": "support", "action": "query", "detail": f"Looked up policy for: {query[:50]}"}],
        )
