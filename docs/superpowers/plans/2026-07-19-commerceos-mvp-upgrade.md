# CommerceOS AI MVP Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade CommerceOS AI from a functional prototype (CSV-backed, 3 agents, no tests) to a production-feeling, portfolio-ready MVP (SQLite-backed, 5 collaborative agents, event-driven, Dockerized, tested).

**Architecture:** Domain-driven `commerceos/` engine package. SQLAlchemy ORM + SQLite persistence. LangGraph supervisor routes to pluggable agents via AgentRegistry. In-process EventBus enables event-driven collaboration (order placed → auto-triggers fraud + inventory + alert chain). Streamlit storefront with admin dashboard and order history.

**Tech Stack:** Python 3.13, Streamlit, LangGraph, LangChain, CrewAI, SQLAlchemy, SQLite, Docker, pytest

## Global Constraints
- All agents use Groq API (set in `.env`)
- SQLite for zero-external-dependency deployment
- Event bus is in-process (no Redis/RabbitMQ)
- All LLM calls go through ChatGroq or CrewAI
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- CSV files remain as seed source — not deleted
- Never commit `.env` with real API key

---

## File Map

```
PHASE A: Structure & Config
  Task 1: commerceos/ package skeleton + config
  Task 2: Refactor existing agents into new structure

PHASE B: Database Layer
  Task 3: SQLAlchemy models + connection
  Task 4: Seed script (CSV → SQLite)
  Task 5: MCP tools refactored for DB

PHASE C: Event System + Observability
  Task 6: EventBus
  Task 7: ActivityTracker + logging
  Task 8: Supervisor refactored to registry

PHASE D: New Agents
  Task 9: Order Agent
  Task 10: Pricing Agent
  Task 11: Event-driven workflows

PHASE E: UI & Storefront
  Task 12: UI components
  Task 13: Cart checkout (buy all items)
  Task 14: Order History page
  Task 15: Admin Dashboard page
  Task 16: Product images + category filter
  Task 17: AI Assistant update

PHASE F: Testing
  Task 18: Test infrastructure + tool tests
  Task 19: Agent tests
  Task 20: Workflow integration tests

PHASE G: Infrastructure + Polish
  Task 21: Docker + docker-compose
  Task 22: .gitignore + pyproject.toml + .env.example
  Task 23: README with architecture diagram
  Task 24: CLAUDE.md update
  Task 25: Git init + structured commits
```

---

## PHASE A: Structure & Config

### Task 1: Create commerceos/ package skeleton + config system

**Files:**
- Create: `commerceos/__init__.py`
- Create: `commerceos/config.py`
- Create: `commerceos/agents/__init__.py`
- Create: `commerceos/agents/base.py`
- Create: `commerceos/agents/registry.py`
- Create: `commerceos/orchestration/__init__.py`
- Create: `commerceos/mcp/__init__.py`
- Create: `commerceos/database/__init__.py`
- Create: `commerceos/observability/__init__.py`

- [ ] **Step 1: Create directory structure**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
mkdir -p commerceos/agents commerceos/orchestration commerceos/mcp commerceos/database commerceos/observability ui/assets/images tests scripts infrastructure
touch commerceos/__init__.py commerceos/agents/__init__.py commerceos/orchestration/__init__.py commerceos/mcp/__init__.py commerceos/database/__init__.py commerceos/observability/__init__.py tests/__init__.py ui/__init__.py
```

- [ ] **Step 2: Create `commerceos/config.py`**
```python
"""Central configuration — single source of truth for all settings."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "qwen/qwen3-32b")
    fraud_llm_model: str = os.getenv("FRAUD_LLM_MODEL", "llama-3.3-70b-versatile")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/commerceos.db")
    store_name: str = "Urban Thread Co."
    tax_rate: float = 0.08
    low_stock_threshold_ratio: float = 1.0
    max_chat_history: int = 10

    @property
    def chroma_store_dir(self) -> str:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma_store")

    @property
    def policy_file(self) -> str:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "refund_policy.txt")


settings = Settings()
```

- [ ] **Step 3: Create `commerceos/agents/base.py`**
```python
"""Abstract base class for all agents."""
from abc import ABC, abstractmethod
from typing import TypedDict


class AgentResult(TypedDict):
    answer: str
    agent: str
    ops_alert: str
    context_used: str
    actions: list[dict]


class BaseAgent(ABC):
    name: str = ""
    description: str = ""
    keywords: list[str] = []

    @abstractmethod
    def run(self, query: str) -> AgentResult:
        ...
```

- [ ] **Step 4: Create `commerceos/agents/registry.py`**
```python
"""AgentRegistry — agents register here, supervisor routes from here."""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from commerceos.agents.base import BaseAgent


class AgentRegistry:
    _agents: dict[str, BaseAgent] = {}

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        cls._agents[agent.name] = agent

    @classmethod
    def get(cls, name: str) -> BaseAgent | None:
        return cls._agents.get(name)

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._agents.keys())

    @classmethod
    def route(cls, query: str) -> str | None:
        query_lower = query.lower()
        best_match = None
        best_len = 0
        for name, agent in cls._agents.items():
            for kw in agent.keywords:
                if kw in query_lower and len(kw) > best_len:
                    best_match = name
                    best_len = len(kw)
        return best_match
```

- [ ] **Step 5: Verify imports work**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "from commerceos.config import settings; print(settings.store_name); from commerceos.agents.base import BaseAgent; print('OK')"
```
Expected: `Urban Thread Co.` and `OK`

---

### Task 2: Refactor existing agents into commerceos package

**Files:**
- Create: `commerceos/agents/support_agent.py`
- Create: `commerceos/agents/inventory_agent.py`
- Create: `commerceos/agents/fraud_agent.py`
- Modify: `commerceos/agents/__init__.py`
- Create: `ui/styling.py` (copy from `utils/styling.py`)

- [ ] **Step 1: Copy styling to new location**
```bash
cp utils/styling.py ui/styling.py
```

- [ ] **Step 2: Create `commerceos/agents/support_agent.py`**
```python
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
```

- [ ] **Step 3: Create `commerceos/agents/inventory_agent.py`**
```python
"""Inventory agent — stock queries + auto-alerts."""
import re
from langchain_groq import ChatGroq
from commerceos.config import settings
from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.mcp.tools import call_tool


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class InventoryAgent(BaseAgent):
    name = "inventory"
    description = "Handles stock and product availability questions"
    keywords = ["stock", "inventory", "available", "restock", "quantity",
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
```

- [ ] **Step 4: Create `commerceos/agents/fraud_agent.py`**
```python
"""Fraud detection agent — CrewAI 2-role sequential crew."""
import crewai.llms.cache as _crew_cache
_crew_cache.mark_cache_breakpoint = lambda msg: msg
from crewai import Agent, Task, Crew, Process, LLM
from commerceos.config import settings
from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.mcp.tools import call_tool

groq_llm = LLM(model=f"groq/{settings.fraud_llm_model}", temperature=0.2)


def extract_order_id(text: str):
    words = text.replace("#", " ").replace(",", " ").split()
    for word in words:
        if word.upper().startswith("O") and word[1:].isdigit():
            return word.upper()
    return None


def format_signal_data(signals: dict) -> str:
    return (
        f"Order ID: {signals['order_id']}\n"
        f"- Velocity check ({signals['velocity_count']} nearby): {signals['velocity_flag']}\n"
        f"- Country mismatch: {signals['country_mismatch']}\n"
        f"- New account + high value: {signals['new_account_high_value']}\n"
        f"- Disposable email: {signals['disposable_email']}\n"
        f"- TOTAL SIGNALS: {signals['total_flags']}/4"
    )


class FraudAgent(BaseAgent):
    name = "fraud"
    description = "Analyzes orders for fraud signals using multi-agent crew"
    keywords = ["fraud", "suspicious", "scam", "fake", "fraudulent", "check order"]

    def run(self, query: str) -> AgentResult:
        order_id = extract_order_id(query)
        actions = [{"agent": "fraud", "action": "analyze", "detail": f"Order: {order_id or 'sweep'}"}]

        if order_id:
            signals = call_tool("get_fraud_signals", order_id=order_id)
            if signals is None:
                return AgentResult(answer=f"Order {order_id} not found.", agent="Fraud Detection Agent",
                                   ops_alert="", context_used="", actions=actions)

            signal_text = format_signal_data(signals)
            crew = self._build_crew(signal_text, order_id)
            raw_result = crew.kickoff()
            report = self._format_report(str(raw_result), signal_text)

            # Persist alert if flagged
            if "REJECT" in str(raw_result).upper() or "HOLD" in str(raw_result).upper():
                try:
                    from commerceos.database.connection import get_session
                    from commerceos.database.models import Alert
                    session = get_session()
                    alert = Alert(type="fraud_flag",
                                  severity="HIGH" if "REJECT" in str(raw_result).upper() else "MEDIUM",
                                  message=f"Order {order_id}: flagged",
                                  source_agent="Fraud Agent")
                    session.add(alert)
                    session.commit()
                    session.close()
                except Exception:
                    pass

            return AgentResult(answer=report, agent="Fraud Detection Agent (CrewAI)",
                               ops_alert=report if "REJECT" in report else "",
                               context_used=signal_text, actions=actions)
        else:
            flagged = call_tool("get_all_flagged_orders")
            if not flagged:
                answer = "No orders triggered 2+ fraud signals."
            else:
                lines = ["### 🔍 Fraud Sweep Results\n"]
                for s in flagged:
                    sev = "🚨 HIGH" if s["total_flags"] >= 3 else "⚠️ MEDIUM"
                    lines.append(f"- {sev} — {s['order_id']}: {s['total_flags']}/4 signals")
                answer = "\n".join(lines)
            return AgentResult(answer=answer, agent="Fraud Detection Agent",
                               ops_alert="", context_used=str(flagged), actions=actions)

    def _build_crew(self, signal_text: str, order_id: str):
        analyst = Agent(role="Fraud Signal Analyst",
                        goal="Objectively interpret raw fraud signals",
                        backstory="Data analyst at e-commerce trust & safety team.",
                        llm=groq_llm, verbose=False)
        adjudicator = Agent(role="Risk Adjudicator",
                            goal="Make final risk decision: APPROVE, HOLD, or REJECT",
                            backstory="Senior fraud risk manager.",
                            llm=groq_llm, verbose=False)
        analyze = Task(description=f"Raw signals for {order_id}:\n{signal_text}\n\nInterpret neutrally.",
                       expected_output="Factual interpretation of signals.", agent=analyst)
        adjudicate = Task(
            description="Based on the Signal Analyst's interpretation, make final decision.\n"
                        "Format:\nDECISION: [APPROVE / HOLD FOR REVIEW / REJECT]\nREASONING: ...",
            expected_output="Decision with reasoning.", agent=adjudicator, context=[analyze])
        return Crew(agents=[analyst, adjudicator], tasks=[analyze, adjudicate],
                    process=Process.sequential, verbose=False)

    def _format_report(self, raw: str, signal_text: str) -> str:
        decision, reasoning = "", ""
        for line in raw.split("\n"):
            if line.upper().startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip()
            elif line.upper().startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
        if not decision:
            return raw
        du = decision.upper()
        badge = "🚨 REJECTED" if "REJECT" in du else ("⚠️ HOLD FOR REVIEW" if "HOLD" in du or "REVIEW" in du else "✅ APPROVED")
        return f"### 🛡️ Fraud Analysis Report\n\n**Risk Decision:** {badge}\n\n**Signal Breakdown:**\n{signal_text}\n\n**Analysis:** {reasoning[:500]}"
```

- [ ] **Step 5: Update `commerceos/agents/__init__.py` to register agents**
```python
from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.agents.registry import AgentRegistry
from commerceos.agents.support_agent import SupportAgent
from commerceos.agents.inventory_agent import InventoryAgent
from commerceos.agents.fraud_agent import FraudAgent

AgentRegistry.register(SupportAgent())
AgentRegistry.register(InventoryAgent())
AgentRegistry.register(FraudAgent())

__all__ = ["BaseAgent", "AgentResult", "AgentRegistry"]
```

- [ ] **Step 6: Verify agent registration**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "from commerceos.agents import AgentRegistry; print('Registered:', AgentRegistry.list())"
```
Expected: `Registered: ['support', 'inventory', 'fraud']`

---

## PHASE B: Database Layer

### Task 3: SQLAlchemy models + connection

**Files:**
- Create: `commerceos/database/models.py`
- Create: `commerceos/database/connection.py`

- [ ] **Step 1: Create `commerceos/database/connection.py`**
```python
"""Database connection management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from commerceos.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = scoped_session(sessionmaker(bind=engine))


def init_db():
    from commerceos.database.models import Base
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
```

- [ ] **Step 2: Create `commerceos/database/models.py`**
```python
"""SQLAlchemy ORM models."""
from datetime import datetime, timezone
from sqlalchemy import (Column, String, Integer, Float, Boolean, Text,
                        DateTime, ForeignKey)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=10)
    image_url = Column(String, default="")
    is_on_sale = Column(Boolean, default=False)
    sale_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    account_age_days = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")
    total_amount = Column(Float, nullable=False)
    tracking_number = Column(String, nullable=True)
    shipping_address = Column(String, default="")
    billing_address = Column(String, default="")
    payment_method = Column(String, default="Credit Card")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    customer = relationship("Customer", backref="orders")
    items = relationship("OrderItem", backref="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    product = relationship("Product")


class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    detail = Column(Text, default="")
    level = Column(String, default="INFO")
    query_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FraudSignal(Base):
    __tablename__ = "fraud_signals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    signal_type = Column(String, nullable=False)
    triggered = Column(Boolean, default=False)
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    analyst_output = Column(Text, nullable=True)
    decision = Column(String, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    severity = Column(String, default="LOW")
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    source_agent = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 3: Verify DB initialization**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "
from commerceos.database.connection import init_db
from commerceos.database.models import Base
from sqlalchemy import create_engine
test_engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(bind=test_engine)
print('Tables:', list(Base.metadata.tables.keys()))
"
```
Expected: 7 table names printed.

---

### Task 4: Seed script — CSV to SQLite

**Files:**
- Create: `commerceos/database/seed.py`
- Create: `scripts/seed.py`

- [ ] **Step 1: Create `commerceos/database/seed.py`**
```python
"""Seed the database from CSV source files."""
import os
import pandas as pd
from commerceos.database.connection import get_session, init_db
from commerceos.database.models import Product, Customer, Order, OrderItem

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
PRODUCTS_CSV = os.path.join(PROJECT_DIR, "data", "products.csv")
ORDERS_CSV = os.path.join(PROJECT_DIR, "data", "orders.csv")


def seed_database():
    init_db()
    session = get_session()

    if session.query(Product).count() > 0:
        print("Database already seeded, skipping.")
        session.close()
        return

    print("Seeding products...")
    products_df = pd.read_csv(PRODUCTS_CSV)
    for _, row in products_df.iterrows():
        session.add(Product(
            id=row["product_id"], name=row["product_name"],
            category=row["category"], price=float(row["price"]),
            stock_quantity=int(row["stock_quantity"]),
            reorder_threshold=int(row["reorder_threshold"]),
            image_url=f"product_{row['product_id'].lower()}.svg",
        ))
    session.commit()
    print(f"  Seeded {len(products_df)} products.")

    print("Seeding orders...")
    orders_df = pd.read_csv(ORDERS_CSV)
    orders_df["order_timestamp"] = pd.to_datetime(orders_df["order_timestamp"])
    order_count = 0

    for _, row in orders_df.iterrows():
        customer = session.query(Customer).filter(Customer.email == row["customer_email"]).first()
        if not customer:
            customer = Customer(name=row["customer_name"], email=row["customer_email"],
                                account_age_days=int(row.get("customer_account_age_days", 0)))
            session.add(customer)
            session.flush()

        if session.query(Order).filter(Order.id == row["order_id"]).first():
            continue

        amount = float(row["order_amount"])
        order = Order(
            id=row["order_id"], customer_id=customer.id, status="delivered",
            total_amount=amount, shipping_address=row.get("shipping_country", ""),
            billing_address=row.get("billing_country", ""),
            payment_method=row.get("payment_method", "Credit Card"),
            created_at=row["order_timestamp"].to_pydatetime(),
        )
        session.add(order)
        session.flush()

        session.add(OrderItem(order_id=order.id, product_id=row["product_id"],
                              quantity=int(row.get("quantity", 1)), unit_price=amount))
        customer.total_orders = (customer.total_orders or 0) + 1
        customer.total_spent = (customer.total_spent or 0) + amount
        order_count += 1

    session.commit()
    session.close()
    print(f"  Seeded {order_count} orders.")
    print("Seeding complete.")


if __name__ == "__main__":
    seed_database()
```

- [ ] **Step 2: Create `scripts/seed.py`**
```python
#!/usr/bin/env python
"""CLI: python scripts/seed.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from commerceos.database.seed import seed_database
seed_database()
```

- [ ] **Step 3: Run seed**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python scripts/seed.py
```
Expected: Seeding messages printed.

- [ ] **Step 4: Verify data persisted**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "
from commerceos.database.connection import get_session
from commerceos.database.models import Product, Customer, Order
s = get_session()
print(f'Products: {s.query(Product).count()}')
print(f'Customers: {s.query(Customer).count()}')
print(f'Orders: {s.query(Order).count()}')
s.close()
"
```

---

### Task 5: MCP tools refactored for SQLite

**Files:**
- Create: `commerceos/mcp/registry.py`
- Create: `commerceos/mcp/tools.py`

- [ ] **Step 1: Create `commerceos/mcp/registry.py`**
```python
"""MCP Tool Registry."""
TOOL_REGISTRY = {}


def register_tool(name: str, func):
    TOOL_REGISTRY[name] = func


def get_tool(name: str):
    return TOOL_REGISTRY.get(name)


def list_tools():
    return list(TOOL_REGISTRY.keys())
```

- [ ] **Step 2: Create `commerceos/mcp/tools.py`**
```python
"""MCP Tool Layer — DB-backed data access for all agents."""
from datetime import timedelta, datetime, timezone
from commerceos.mcp.registry import register_tool, get_tool
from commerceos.database.connection import get_session
from commerceos.database.models import Product, Customer, Order, OrderItem


def get_all_products() -> list[dict]:
    session = get_session()
    products = session.query(Product).all()
    result = [{"product_id": p.id, "product_name": p.name, "category": p.category,
               "price": p.price, "stock_quantity": p.stock_quantity,
               "reorder_threshold": p.reorder_threshold, "image_url": p.image_url,
               "is_on_sale": p.is_on_sale, "sale_price": p.sale_price} for p in products]
    session.close()
    return result


def search_products(query: str) -> list[dict]:
    session = get_session()
    products = session.query(Product).all()
    words = query.lower().split()
    result = []
    for p in products:
        if any(w in p.name.lower() for w in words):
            result.append({"product_id": p.id, "product_name": p.name, "category": p.category,
                           "price": p.price, "stock_quantity": p.stock_quantity,
                           "reorder_threshold": p.reorder_threshold, "image_url": p.image_url,
                           "is_on_sale": p.is_on_sale, "sale_price": p.sale_price})
    session.close()
    return result


def get_low_stock_products() -> list[dict]:
    session = get_session()
    products = session.query(Product).filter(Product.stock_quantity <= Product.reorder_threshold).all()
    result = [{"product_id": p.id, "product_name": p.name, "stock_quantity": p.stock_quantity,
               "reorder_threshold": p.reorder_threshold} for p in products]
    session.close()
    return result


def get_product_by_id(product_id: str) -> dict | None:
    session = get_session()
    p = session.query(Product).filter(Product.id == product_id).first()
    if not p:
        session.close()
        return None
    result = {"product_id": p.id, "product_name": p.name, "category": p.category,
              "price": p.price, "stock_quantity": p.stock_quantity,
              "reorder_threshold": p.reorder_threshold, "image_url": p.image_url,
              "is_on_sale": p.is_on_sale, "sale_price": p.sale_price}
    session.close()
    return result


def get_order_by_id(order_id: str) -> dict | None:
    session = get_session()
    o = session.query(Order).filter(Order.id == order_id.upper()).first()
    if not o:
        session.close()
        return None
    c = session.query(Customer).filter(Customer.id == o.customer_id).first()
    items = session.query(OrderItem).filter(OrderItem.order_id == o.id).all()
    result = {"order_id": o.id, "customer_name": c.name if c else "",
              "customer_email": c.email if c else "", "product_id": items[0].product_id if items else "",
              "order_amount": o.total_amount, "quantity": sum(i.quantity for i in items) if items else 1,
              "order_timestamp": str(o.created_at), "shipping_country": o.shipping_address,
              "billing_country": o.billing_address, "status": o.status,
              "tracking_number": o.tracking_number}
    session.close()
    return result


def get_fraud_signals(order_id: str) -> dict | None:
    session = get_session()
    order = session.query(Order).filter(Order.id == order_id.upper()).first()
    if not order:
        session.close()
        return None
    customer = session.query(Customer).filter(Customer.id == order.customer_id).first()
    if not customer:
        session.close()
        return {"order_id": order_id, "velocity_flag": False, "velocity_count": 0,
                "country_mismatch": False, "new_account_high_value": False,
                "disposable_email": False, "total_flags": 0}

    window_start = order.created_at - timedelta(minutes=15)
    window_end = order.created_at + timedelta(minutes=15)
    nearby = session.query(Order).filter(Order.customer_id == customer.id,
                                         Order.created_at >= window_start,
                                         Order.created_at <= window_end).count()
    velocity_flag = nearby > 1
    country_mismatch = order.shipping_address != order.billing_address if order.shipping_address else False
    new_account_high_value = customer.account_age_days <= 3 and order.total_amount >= 100
    disposable_markers = ["tempmail", "guest", "temp", "10minutemail", "throwaway"]
    disposable_email = any(m in customer.email.lower() for m in disposable_markers)
    total = sum([velocity_flag, country_mismatch, new_account_high_value, disposable_email])
    session.close()
    return {"order_id": order_id, "velocity_flag": velocity_flag, "velocity_count": nearby,
            "country_mismatch": country_mismatch, "new_account_high_value": new_account_high_value,
            "disposable_email": disposable_email, "total_flags": total}


def get_all_flagged_orders() -> list[dict]:
    session = get_session()
    orders = session.query(Order).all()
    flagged = []
    for o in orders:
        sig = get_fraud_signals(o.id)
        if sig and sig["total_flags"] >= 2:
            flagged.append(sig)
    session.close()
    return flagged


_next_order_num = [2016]


def append_order(customer_name: str, customer_email: str, shipping_country: str,
                 product_id: str, quantity: int = 1) -> dict:
    from commerceos.orchestration.event_bus import event_bus
    session = get_session()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            session.close()
            return {"error": f"Product {product_id} not found"}

        customer = session.query(Customer).filter(Customer.email == customer_email).first()
        if not customer:
            customer = Customer(name=customer_name, email=customer_email, account_age_days=0)
            session.add(customer)
            session.flush()

        order_id = f"O{_next_order_num[0]}"
        _next_order_num[0] += 1
        total = round(product.price * quantity, 2)
        now = datetime.now(timezone.utc)

        order = Order(id=order_id, customer_id=customer.id, status="pending",
                      total_amount=total, shipping_address=shipping_country,
                      billing_address=shipping_country, created_at=now)
        session.add(order)
        session.flush()

        session.add(OrderItem(order_id=order_id, product_id=product_id,
                              quantity=quantity, unit_price=product.price))
        session.commit()

        # Emit event for auto-triggered workflows
        try:
            event_bus.emit("order.created", {
                "order_id": order_id, "customer_email": customer_email,
                "product_id": product_id, "quantity": quantity,
            })
        except Exception:
            pass

        session.close()
        return {"order_id": order_id, "product_name": product.name, "total": total}
    except Exception as e:
        session.rollback()
        session.close()
        return {"error": str(e)}


# Register all tools
for _name, _func in [
    ("get_all_products", get_all_products), ("search_products", search_products),
    ("get_low_stock_products", get_low_stock_products),
    ("get_product_by_id", get_product_by_id), ("get_order_by_id", get_order_by_id),
    ("get_fraud_signals", get_fraud_signals),
    ("get_all_flagged_orders", get_all_flagged_orders),
    ("append_order", append_order),
]:
    register_tool(_name, _func)


def call_tool(tool_name: str, **kwargs):
    func = get_tool(tool_name)
    if func is None:
        raise ValueError(f"Unknown tool: {tool_name}")
    return func(**kwargs)
```

- [ ] **Step 3: Verify tools work**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "
from commerceos.mcp.tools import call_tool
print('Products:', len(call_tool('get_all_products')))
print('Order O2001:', call_tool('get_order_by_id', order_id='O2001'))
print('Low stock:', len(call_tool('get_low_stock_products')))
"
```

---

## PHASE C: Event System + Observability

### Task 6: EventBus

**Files:**
- Create: `commerceos/orchestration/event_bus.py`

- [ ] **Step 1: Create `commerceos/orchestration/event_bus.py`**
```python
"""In-process event bus — pub/sub for agent collaboration."""
from typing import Callable
from collections import defaultdict
import logging


class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event_type: str, handler: Callable) -> None:
        self._listeners[event_type].append(handler)

    def emit(self, event_type: str, data: dict | None = None) -> None:
        data = data or {}
        for handler in self._listeners.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                logging.error(f"Event handler error for {event_type}: {e}")

    def remove(self, event_type: str, handler: Callable) -> None:
        self._listeners[event_type] = [h for h in self._listeners[event_type] if h != handler]

    def clear(self) -> None:
        self._listeners.clear()


event_bus = EventBus()
```

- [ ] **Step 2: Test EventBus**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "
from commerceos.orchestration.event_bus import EventBus
bus = EventBus()
results = []
bus.on('test', lambda d: results.append(d['msg']))
bus.emit('test', {'msg': 'hello'})
bus.emit('test', {'msg': 'world'})
assert results == ['hello', 'world']
print('EventBus OK:', results)
"
```

---

### Task 7: ActivityTracker + structured logging

**Files:**
- Create: `commerceos/observability/logger.py`
- Create: `commerceos/observability/activity_tracker.py`

- [ ] **Step 1: Create `commerceos/observability/logger.py`**
```python
"""Structured logging."""
import sys
import json
import logging
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "level": record.levelname, "logger": record.name,
                 "message": record.getMessage()}
        for attr in ("agent", "action"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        return json.dumps(entry)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
```

- [ ] **Step 2: Create `commerceos/observability/activity_tracker.py`**
```python
"""Records every agent action → AgentLog table."""
from commerceos.observability.logger import get_logger
from commerceos.database.connection import get_session
from commerceos.database.models import AgentLog

_logger = get_logger("activity_tracker")


def track(agent_name: str, action: str, detail: str = "",
          level: str = "INFO", query_id: str | None = None) -> None:
    _logger.info(f"[{agent_name}] {action}: {detail[:200]}",
                 extra={"agent": agent_name, "action": action})
    try:
        session = get_session()
        session.add(AgentLog(agent_name=agent_name, action=action,
                             detail=detail[:500], level=level, query_id=query_id))
        session.commit()
        session.close()
    except Exception as e:
        _logger.warning(f"Failed to persist agent log: {e}")
```

- [ ] **Step 3: Verify ActivityTracker**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "
from commerceos.observability.activity_tracker import track
from commerceos.database.connection import get_session
from commerceos.database.models import AgentLog
track('test', 'test_action', 'testing 123')
s = get_session()
print('Log entries:', s.query(AgentLog).count())
s.close()
"
```
Expected: `Log entries: 1`

---

### Task 8: Supervisor refactored to use AgentRegistry

**Files:**
- Create: `commerceos/orchestration/supervisor.py`
- Root `supervisor.py` kept as deprecation shim

- [ ] **Step 1: Create `commerceos/orchestration/supervisor.py`**
```python
"""LangGraph Supervisor with AgentRegistry routing + MemorySaver."""
import re
from typing import TypedDict, Literal, Annotated
from operator import add
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from commerceos.config import settings
from commerceos.agents import AgentRegistry
from commerceos.observability.activity_tracker import track


class GraphState(TypedDict):
    user_query: str
    route: str
    agent_name: str
    answer: str
    ops_alert: str
    context_used: str
    history: Annotated[list, add]


def supervisor_node(state: GraphState) -> GraphState:
    query = state["user_query"]
    query_lower = query.lower()

    route_match = AgentRegistry.route(query)
    if route_match:
        state["route"] = route_match
        track("Supervisor", "route", f"Keyword → {route_match}: {query[:50]}")
        return state

    history = state.get("history", [])
    history_text = ""
    if history:
        recent = history[-3:]
        history_text = "Recent:\n" + "\n".join([f"- [{h['agent']}] Q: {h['query'][:50]}" for h in recent])

    agents_list = ", ".join(AgentRegistry.list())
    prompt = (
        f"You route queries at {settings.store_name} to: {agents_list}.\n"
        f"- support: orders, refunds, returns, shipping, policy\n"
        f"- inventory: stock levels, availability\n"
        f"- fraud: suspicious orders, fraud checks\n"
        f"- order: order status, tracking, cancellation\n"
        f"- pricing: sales, discounts, deals\n"
        f"{history_text}\nReply with ONE word.\nQuery: \"{query}\"\nCategory:"
    )

    llm = ChatGroq(model=settings.llm_model, temperature=0)
    response = llm.invoke(prompt)
    decision = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip().lower()
    valid = AgentRegistry.list()
    state["route"] = decision if decision in valid else "support"
    return state


def route_decision(state: GraphState) -> Literal["support", "inventory", "fraud", "order", "pricing"]:
    return state["route"]


def _record_history(state: GraphState, result: dict) -> GraphState:
    state["agent_name"] = result.get("agent", "")
    state["answer"] = result.get("answer", "")
    state["ops_alert"] = result.get("ops_alert", "")
    state["context_used"] = result.get("context_used", "")
    state["history"] = [{"query": state["user_query"], "agent": result.get("agent", ""), "answer": result.get("answer", "")[:100]}]
    return state


def _run_agent(state: GraphState, agent_name: str) -> GraphState:
    agent = AgentRegistry.get(agent_name)
    if not agent:
        return _error_state(state, f"{agent_name} agent not available")
    try:
        result = agent.run(state["user_query"])
        track(agent_name.capitalize(), "query", state["user_query"][:80])
        return _record_history(state, result)
    except Exception as e:
        return _error_state(state, f"{agent_name} error: {e}")


def support_node(state): return _run_agent(state, "support")
def inventory_node(state): return _run_agent(state, "inventory")
def fraud_node(state): return _run_agent(state, "fraud")
def order_node(state): return _run_agent(state, "order")
def pricing_node(state): return _run_agent(state, "pricing")


def _error_state(state: GraphState, message: str) -> GraphState:
    state["agent_name"] = "System"
    state["answer"] = f"I ran into a problem: {message}\n\nPlease try again."
    state["ops_alert"] = ""
    state["context_used"] = ""
    state["history"] = [{"query": state["user_query"], "agent": "System", "answer": message}]
    return state


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("supervisor", supervisor_node)
    for name in ["support", "inventory", "fraud", "order", "pricing"]:
        graph.add_node(name, lambda s, n=name: _run_agent(s, n))
    graph.set_entry_point("supervisor")
    route_map = {name: name for name in ["support", "inventory", "fraud", "order", "pricing"]}
    graph.add_conditional_edges("supervisor", route_decision, route_map)
    for name in route_map:
        graph.add_edge(name, END)
    return graph.compile(checkpointer=MemorySaver())


commerceos_graph = build_graph()


def handle_query(user_query: str, thread_id: str = "default-session") -> dict:
    if not user_query or not user_query.strip():
        return {"user_query": "", "route": "", "agent_name": "System",
                "answer": "Please type a question.", "ops_alert": "",
                "context_used": "", "history": []}
    initial = {"user_query": user_query, "route": "", "agent_name": "",
               "answer": "", "ops_alert": "", "context_used": "", "history": []}
    result = commerceos_graph.invoke(initial, {"configurable": {"thread_id": thread_id}})
    return result
```

---

## PHASE D: New Agents

### Task 9: Order Agent

**Files:**
- Create: `commerceos/agents/order_agent.py`
- Modify: `commerceos/agents/__init__.py`

- [ ] **Step 1: Create `commerceos/agents/order_agent.py`**
```python
"""Order Management Agent — lifecycle, tracking, cancellation."""
import re, random, string
from datetime import datetime, timezone
from langchain_groq import ChatGroq
from commerceos.config import settings
from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.database.connection import get_session
from commerceos.database.models import Order, Customer


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
    keywords = ["order status", "track my order", "cancel order", "where is my",
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
                order.updated_at = datetime.now(timezone.utc)
                session.commit()
                session.close()
                return AgentResult(answer=f"✅ Order {order_id} cancelled.",
                                   agent="Order Management Agent",
                                   ops_alert=f"Order {order_id} cancelled",
                                   context_used="", actions=actions + [{"agent": "order", "action": "cancel", "detail": order_id}])
            session.close()
            return AgentResult(answer=f"Order {order_id} is '{order.status}' and cannot be cancelled.",
                               agent="Order Management Agent", ops_alert="", context_used="", actions=actions)

        if order.status in ["confirmed", "processing"] and not order.tracking_number:
            order.tracking_number = _generate_tracking()
            order.status = "shipped"
            order.updated_at = datetime.now(timezone.utc)
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
```

- [ ] **Step 2: Update `commerceos/agents/__init__.py`**
```python
from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.agents.registry import AgentRegistry
from commerceos.agents.support_agent import SupportAgent
from commerceos.agents.inventory_agent import InventoryAgent
from commerceos.agents.fraud_agent import FraudAgent
from commerceos.agents.order_agent import OrderAgent

AgentRegistry.register(SupportAgent())
AgentRegistry.register(InventoryAgent())
AgentRegistry.register(FraudAgent())
AgentRegistry.register(OrderAgent())

__all__ = ["BaseAgent", "AgentResult", "AgentRegistry"]
```

- [ ] **Step 3: Verify**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "from commerceos.agents import AgentRegistry; print(AgentRegistry.list())"
```
Expected: `['support', 'inventory', 'fraud', 'order']`

---

### Task 10: Pricing Agent

**Files:**
- Create: `commerceos/agents/pricing_agent.py`
- Modify: `commerceos/agents/__init__.py`

- [ ] **Step 1: Create `commerceos/agents/pricing_agent.py`**
```python
"""Pricing Agent — dynamic pricing, sale suggestions."""
import re
from langchain_groq import ChatGroq
from commerceos.config import settings
from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.database.connection import get_session
from commerceos.database.models import Product, OrderItem


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class PricingAgent(BaseAgent):
    name = "pricing"
    description = "Dynamic pricing, sale analysis, slow-moving inventory"
    keywords = ["sale", "discount", "deal", "price", "pricing", "promotion",
                "cheap", "on sale", "good deal", "any deals"]

    def run(self, query: str) -> AgentResult:
        session = get_session()
        products = session.query(Product).all()
        on_sale = [p for p in products if p.is_on_sale]
        actions = [{"agent": "pricing", "action": "analyze", "detail": query[:80]}]

        sale_context = ""
        if on_sale:
            lines = ["### 🏷️ Current Sales\n"]
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
```

- [ ] **Step 2: Update `commerceos/agents/__init__.py`**
```python
from commerceos.agents.base import BaseAgent, AgentResult
from commerceos.agents.registry import AgentRegistry
from commerceos.agents.support_agent import SupportAgent
from commerceos.agents.inventory_agent import InventoryAgent
from commerceos.agents.fraud_agent import FraudAgent
from commerceos.agents.order_agent import OrderAgent
from commerceos.agents.pricing_agent import PricingAgent

AgentRegistry.register(SupportAgent())
AgentRegistry.register(InventoryAgent())
AgentRegistry.register(FraudAgent())
AgentRegistry.register(OrderAgent())
AgentRegistry.register(PricingAgent())

__all__ = ["BaseAgent", "AgentResult", "AgentRegistry"]
```

- [ ] **Step 3: Verify**
```bash
cd /c/Users/New\ Moon/Desktop/commerceos-ai
python -c "from commerceos.agents import AgentRegistry; print('Agents:', AgentRegistry.list())"
```
Expected: 5 agents listed.

---

### Task 11: Event-driven workflows

**Files:**
- Create: `commerceos/orchestration/workflows.py`
- Modify: `commerceos/agents/__init__.py`

- [ ] **Step 1: Create `commerceos/orchestration/workflows.py`**
```python
"""Event-driven workflow definitions."""
from commerceos.orchestration.event_bus import event_bus
from commerceos.observability.activity_tracker import track


def register_event_handlers():
    @event_bus.on("order.created")
    def handle_order_created(data: dict):
        order_id = data.get("order_id", "")
        track("Workflow", "event", f"order.created: {order_id}")

        from commerceos.agents import AgentRegistry
        fraud = AgentRegistry.get("fraud")
        if fraud:
            try:
                result = fraud.run(f"Check order {order_id} for fraud")
                track("Workflow", "fraud_check", f"Order {order_id}: {result['answer'][:60]}")
                if "REJECT" in result["answer"] or "HOLD" in result["answer"]:
                    from commerceos.database.connection import get_session
                    from commerceos.database.models import Alert
                    s = get_session()
                    s.add(Alert(type="fraud_flag",
                                severity="HIGH" if "REJECT" in result["answer"] else "MEDIUM",
                                message=f"Order {order_id} flagged by auto-fraud check",
                                source_agent="Workflow"))
                    s.commit()
                    s.close()
            except Exception as e:
                track("Workflow", "fraud_error", str(e), level="ERROR")

        from commerceos.database.connection import get_session
        from commerceos.database.models import Product, OrderItem, Order as OrderModel
        s = get_session()
        order = s.query(OrderModel).filter(OrderModel.id == order_id).first()
        if order:
            items = s.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            for item in items:
                prod = s.query(Product).filter(Product.id == item.product_id).first()
                if prod:
                    prod.stock_quantity -= item.quantity
                    if prod.stock_quantity <= prod.reorder_threshold:
                        from commerceos.database.models import Alert
                        s.add(Alert(type="low_stock", severity="MEDIUM",
                                    message=f"{prod.name} low ({prod.stock_quantity} left)",
                                    source_agent="Workflow"))
            if order.status == "pending":
                order.status = "confirmed"
                from datetime import datetime, timezone
                order.updated_at = datetime.now(timezone.utc)
            s.commit()
        s.close()

    track("Workflow", "init", "Event handlers registered")
```

- [ ] **Step 2: Update `commerceos/agents/__init__.py` to wire up events**
Add at the bottom:
```python
from commerceos.orchestration.workflows import register_event_handlers
register_event_handlers()
```

---

## PHASE E: UI & Storefront

### Task 12: UI components

**Files:**
- Create: `ui/components.py`

- [ ] **Step 1: Create `ui/components.py`**
```python
"""Reusable Streamlit UI components."""
import streamlit as st
from datetime import datetime, timezone


def metric_card(label: str, value, delta="", help_text=""):
    delta_html = f'<div style="font-size:0.75rem;color:#e94560;">{delta}</div>' if delta else ""
    st.markdown(
        f'<div style="background:white;padding:1rem;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);text-align:center;">'
        f'<div style="font-size:0.8rem;color:#636e72;text-transform:uppercase;font-weight:600;">{label}</div>'
        f'<div style="font-size:1.8rem;font-weight:700;color:#1a1a2e;margin:0.5rem 0;">{value}</div>'
        f'{delta_html}</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    colors = {"pending": "#f59e0b", "confirmed": "#3b82f6", "processing": "#636e72",
              "shipped": "#8b5cf6", "delivered": "#10b981", "cancelled": "#ef4444"}
    c = colors.get(status.lower(), "#636e72")
    return f'<span style="background:{c}20;color:{c};padding:0.2rem 0.6rem;border-radius:20px;font-size:0.8rem;font-weight:600;">{status.upper()}</span>'


def format_uptime() -> str:
    if "_startup" not in st.session_state:
        st.session_state._startup = datetime.now(timezone.utc)
    delta = datetime.now(timezone.utc) - st.session_state._startup
    h, r = divmod(int(delta.total_seconds()), 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"
```

---

### Task 13 through Task 25

*(Tasks 13-25 follow the same pattern — detailed code for each file is in the spec at `docs/superpowers/specs/2026-07-19-commerceos-mvp-design.md`)*

The remaining tasks are:

- **Task 13:** Update cart to buy all items + emit `order.created` event
- **Task 14:** Order History page (email lookup, order details, fraud results)
- **Task 15:** Admin Dashboard (fraud alerts, stock overview, agent log, quick actions)
- **Task 16:** Product images generator + category filter in app.py
- **Task 17:** AI Assistant with new imports + Pricing example
- **Task 18:** Test infrastructure (conftest.py) + tool tests
- **Task 19:** Agent registration + routing tests
- **Task 20:** Workflow integration tests
- **Task 21:** Dockerfile + docker-compose.yml + entrypoint.sh
- **Task 22:** pyproject.toml, .gitignore, .env.example cleanup
- **Task 23:** README + docs/architecture.md
- **Task 24:** CLAUDE.md update
- **Task 25:** Git init + structured commit history

See the spec document for complete code for each of these.
```

