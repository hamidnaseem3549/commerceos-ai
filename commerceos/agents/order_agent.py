"""Order Management Agent — lifecycle, tracking, cancellation."""
import random
import re
import string
from datetime import UTC, datetime

from langchain_groq import ChatGroq

from commerceos.agents.base import AgentResult, BaseAgent
from commerceos.config import settings
from commerceos.database.connection import get_session
from commerceos.database.models import Order


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_order_id(text: str):
    words = text.replace("#", " ").replace(",", " ").split()
    for word in words:
        if word.upper().startswith("O") and word[1:].isdigit():
            return word.upper()
    return None


def _generate_tracking() -> str:
    prefix = random.choice(["1Z", "TRK", "SHIP"])
    return prefix + "".join(random.choices(string.digits, k=9))


class OrderAgent(BaseAgent):
    name = "order"
    description = "Manages order lifecycle — status, tracking, cancellation"
    keywords = ["order status", "track my order", "cancel order", "where is my order",  # noqa: RUF012
                "shipping", "tracking", "order update", "order details"]

    def run(self, query: str) -> AgentResult:
        order_id = extract_order_id(query)
        actions = [{"agent": "order", "action": "query", "detail": query[:80]}]

        if not order_id:
            session = get_session()
            recent = session.query(Order).order_by(Order.created_at.desc()).limit(5).all()
            session.close()
            if recent:
                lines = ["Recent orders:\n"] + [f"- {o.id}: ${o.total_amount} — {o.status}" for o in recent]
                return AgentResult(answer="\n".join(lines), agent="Order Management Agent",
                                   ops_alert="", context_used="", actions=actions)
            return AgentResult(answer="No orders found.", agent="Order Management Agent",
                               ops_alert="", context_used="", actions=actions)

        session = get_session()
        order = session.query(Order).filter(Order.id == order_id).first()
        if not order:
            session.close()
            return AgentResult(answer=f"Order {order_id} not found. Please check the ID.",
                               agent="Order Management Agent", ops_alert="", context_used="", actions=actions)

        if any(w in query.lower() for w in ["cancel", "stop", "void"]):
            if order.status in ["pending", "confirmed"]:
                order.status = "cancelled"
                order.updated_at = datetime.now(UTC)
                session.commit()
                session.close()
                return AgentResult(answer=f"Order {order_id} cancelled.",
                                   agent="Order Management Agent",
                                   ops_alert=f"Order {order_id} cancelled",
                                   context_used="",
                                   actions=actions + [{"agent": "order", "action": "cancel", "detail": order_id}])
            session.close()
            return AgentResult(answer=f"Order {order_id} is '{order.status}' and cannot be cancelled.",
                               agent="Order Management Agent", ops_alert="", context_used="", actions=actions)

        if order.status in ["confirmed", "processing"] and not order.tracking_number:
            order.tracking_number = _generate_tracking()
            order.status = "shipped"
            order.updated_at = datetime.now(UTC)
            session.commit()

        context = (f"Order {order.id}: Status={order.status}, Amount=${order.total_amount}, "
                   f"Tracking={order.tracking_number or 'N/A'}")
        session.close()

        llm = ChatGroq(model=settings.llm_model, temperature=settings.llm_temperature)
        answer = strip_think_tags(llm.invoke(
            f"Order info:\n{context}\nCustomer asked: {query}\nReply helpfully:"
        ).content)
        return AgentResult(answer=answer, agent="Order Management Agent",
                           ops_alert="", context_used=context, actions=actions)
