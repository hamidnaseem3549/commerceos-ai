"""Pricing Agent — dynamic pricing, sale suggestions."""
import re

from langchain_groq import ChatGroq

from commerceos.agents.base import AgentResult, BaseAgent
from commerceos.config import settings
from commerceos.database.connection import get_session
from commerceos.database.models import OrderItem, Product


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class PricingAgent(BaseAgent):
    name = "pricing"
    description = "Dynamic pricing, sale analysis, slow-moving inventory"
    keywords = ["sale", "discount", "deal", "price", "pricing", "promotion",  # noqa: RUF012
                "cheap", "on sale", "good deal", "any deals"]

    def run(self, query: str) -> AgentResult:
        session = get_session()
        products = session.query(Product).all()
        on_sale = [p for p in products if p.is_on_sale]
        actions = [{"agent": "pricing", "action": "analyze", "detail": query[:80]}]

        sale_context = ""
        if on_sale:
            lines = ["### \U0001f6d2 Current Sales\n"]
            for p in on_sale:
                discount = int((1 - p.sale_price / p.price) * 100) if p.sale_price else 0
                lines.append(f"- **{p.name}**: ~~${p.price:.2f}~~ **${p.sale_price:.2f}** ({discount}% off!)")
            sale_context = "\n".join(lines)
        else:
            sale_context = "No products currently on sale."

        if any(w in query.lower() for w in ["sale", "deal", "discount", "promotion"]):
            if on_sale:
                session.close()
                return AgentResult(answer=sale_context + "\n\nShop the sale on our Home page!",
                                   agent="Pricing Agent", ops_alert="", context_used=sale_context, actions=actions)
            llm = ChatGroq(model=settings.llm_model, temperature=settings.llm_temperature)
            answer = strip_think_tags(llm.invoke(
                f"No active sales at {settings.store_name}. Be cheerful and encourage browsing. Query: {query}"
            ).content)
            session.close()
            return AgentResult(answer=answer, agent="Pricing Agent", ops_alert="", context_used=sale_context, actions=actions)

        session.close()
        llm = ChatGroq(model=settings.llm_model, temperature=settings.llm_temperature)
        answer = strip_think_tags(llm.invoke(f"{sale_context}\nAnswer customer naturally. Query: {query}").content)
        return AgentResult(answer=answer, agent="Pricing Agent", ops_alert="", context_used=sale_context, actions=actions)


def analyze_and_apply_sales() -> list[str]:
    """Apply 20% off to slow-moving products. Called from admin dashboard."""
    session = get_session()
    products = session.query(Product).all()
    items = session.query(OrderItem).all()
    sales_count = {p.id: 0 for p in products}
    for item in items:
        if item.product_id in sales_count:
            sales_count[item.product_id] += item.quantity
    applied = []
    for p in products:
        if sales_count.get(p.id, 0) < 3 and p.stock_quantity > p.reorder_threshold * 2 and not p.is_on_sale:
            p.is_on_sale = True
            p.sale_price = round(p.price * 0.8, 2)
            applied.append(p.name)
    session.commit()
    session.close()
    return applied
