<div align="center">
  <br/>
  <h1>🛍️ CommerceOS AI</h1>
  <p><strong>Autonomous Multi-Agent E-Commerce Operations System</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.13-%233776AB?logo=python&logoColor=white" alt="Python 3.13"/>
    <img src="https://img.shields.io/badge/LangGraph-0.4-%2300B4D8?logo=langchain&logoColor=white" alt="LangGraph 0.4"/>
    <img src="https://img.shields.io/badge/CrewAI-0.105-%23FF6B35" alt="CrewAI 0.105"/>
    <img src="https://img.shields.io/badge/Streamlit-1.40-%23FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit 1.40"/>
    <img src="https://img.shields.io/badge/FastAPI-0.115-%23009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
    <img src="https://img.shields.io/badge/Next.js-14.2-%23000000?logo=next.js&logoColor=white" alt="Next.js 14"/>
    <br/>
    <img src="https://img.shields.io/badge/CI-passing-%2328a745" alt="CI passing"/>
    <img src="https://img.shields.io/badge/coverage-80%25-%23a0c334" alt="Coverage 80%"/>
    <img src="https://img.shields.io/badge/code%20style-ruff-%23D32F2F" alt="Ruff"/>
    <img src="https://img.shields.io/badge/license-MIT-%23blue" alt="MIT License"/>
  </p>
  <br/>
</div>

## 📋 Overview

CommerceOS AI is an **autonomous, event-driven e-commerce platform** powered by **five specialized AI agents** working in orchestration. Unlike traditional e-commerce systems where features are hardcoded, this platform uses a **LangGraph supervisor** to route user intents to the right agent, a **CrewAI pipeline** for fraud analysis, and an **EventBus** for agent-to-agent collaboration.

> **Five AI agents. One intelligent storefront. Zero humans in the loop.**

---

## 🧠 System Architecture

```
                         ┌─────────────────────────────────────┐
                         │         NEXT.JS STOREFRONT           │
                         │   Products · Cart · AI Chat · Admin   │
                         └───────────────┬─────────────────────┘
                                         │ HTTP / SSE
                         ┌───────────────▼─────────────────────┐
                         │        FASTAPI REST LAYER            │
                         │     (9 MCP tools · SSE streaming)    │
                         └───────────────┬─────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │         LANGGRAPH SUPERVISOR             │
                    │  AgentRegistry routing · MemorySaver     │
                    │  (keyword pre-check → LLM fallback)      │
                    └──────┬──────┬──────┬──────┬──────┬──────┘
                           │      │      │      │      │
                    ┌──────▼┐ ┌──▼──┐ ┌─▼──┐ ┌─▼───┐ ┌▼──────┐
                    │Support│ │Inv. │ │Frau│ │Order│ │Pricing│
                    │(RAG)  │ │(LLM)│ │(Crw│ │(LLM)│ │(LLM)  │
                    └──────┘ └─────┘ └────┘ └─────┘ └───────┘
                           │      │      │      │      │
                    ┌──────▼──────▼──────▼──────▼──────▼──────┐
                    │        MCP TOOL LAYER (SQLAlchemy)       │
                    │  Products · Orders · Customers · Logs    │
                    └───────────────────┬──────────────────────┘
                                        │
                    ┌───────────────────▼──────────────────────┐
                    │         EVENT BUS + WORKFLOWS             │
                    │   order.created → fraud check → deduct    │
                    │   → stock alert → status update → log     │
                    └──────────────────────────────────────────┘
```

---

## 🤖 The Five Agents

| Agent | Framework | Core Capability | Trigger |
|-------|-----------|----------------|---------|
| **🎧 Support** | LangChain + ChromaDB RAG | Policy Q&A, returns, order lookups grounded in actual documents | `"Can I return a damaged item?"` |
| **📦 Inventory** | LangChain + Groq | Live stock queries, low-stock alerts, reorder recommendations | `"Do you have white t-shirts?"` |
| **🛡️ Fraud** | CrewAI (2-role sequential) | Signal Analyst → Risk Adjudicator pipeline with scored decisions | `"Check order O2004 for fraud"` |
| **📋 Order** | LangChain | Full lifecycle: tracking, cancellation, shipment generation | `"Where is my order O2001?"` |
| **🏷️ Pricing** | LangChain | Sale suggestions, slow-mover analysis, dynamic markdown | `"Any items on sale?"` |

### Agent Collaboration Flow

When a customer places an order, the system doesn't just save a row — it orchestrates a multi-agent workflow:

```
Order Placed
  │
  ├─▶ Fraud Agent (CrewAI) analyzes signals
  │     ├─ Velocity check (15-min window)
  │     ├─ Country mismatch detection
  │     ├─ New-account + high-value scoring
  │     └─ Disposable email detection
  │
  ├─▶ Inventory Agent deducts stock
  │     └─ Triggers low-stock alert if threshold hit
  │
  └─▶ Order status → confirmed/pending
        └─ All steps logged to AgentLog
        └─ Admin Dashboard updates in real-time
```

---

## ⚙️ Technical Deep Dive

### LangGraph Supervisor
The routing layer uses a **StateGraph** with configurable checkpoints (MemorySaver). Each conversation gets a thread_id for continuity. Routing happens in two stages:
1. **Keyword pre-check** — `AgentRegistry.route()` matches against agent keyword lists (longest match wins)
2. **LLM fallback** — If no keyword matches, `ChatGroq` classifies the intent

### CrewAI Fraud Pipeline
The fraud agent runs a **two-role sequential crew**:
- **Signal Analyst** — Objectively interprets raw fraud signals
- **Risk Adjudicator** — Makes final decision: `APPROVE` / `HOLD` / `REJECT`

Each flagged order creates a persistent `Alert` in the database, visible in the admin dashboard.

### EventBus Architecture
The in-process pub/sub system enables **decoupled agent collaboration**:
```python
event_bus.emit("order.created", {"order_id": "O2001"})
# Automatically triggers: fraud check → inventory deduct → stock alert
```

### MCP Tool Layer
Nine database-backed tools provide a **unified data access layer** for all agents:
`get_all_products`, `search_products`, `get_low_stock_products`, `get_product_by_id`, `get_order_by_id`, `get_orders_by_email`, `get_fraud_signals`, `get_all_flagged_orders`, `append_order`

---

## 🧩 Technology Deep Dive

### LangGraph — Orchestration Spine

The entire agent routing system is built on **LangGraph's StateGraph**, a stateful graph-based orchestration framework. Each user query flows through a directed graph where the **Supervisor Node** decides routing, and the selected **Agent Node** processes the request.

```python
graph = StateGraph(GraphState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("fraud", lambda s: _run_agent(s, "fraud"))
graph.set_entry_point("supervisor")
graph.add_conditional_edges("supervisor", route_decision, route_map)
```

**MemorySaver** checkpointer maintains per-session conversation history — enabling context-aware multi-turn interactions without external databases:

```python
compiled = graph.compile(checkpointer=MemorySaver())
result = compiled.invoke(initial, {"configurable": {"thread_id": thread_id}})
```

### LangChain — Agent Intelligence

Each specialist agent (Support, Inventory, Order, Pricing) uses **LangChain** with **ChatGroq** to power its LLM interactions. The framework provides:
- **Prompt templating** — Consistent system prompts per agent role
- **Output parsing** — Structured responses from LLM outputs
- **Integration layer** — Unified interface across LLM providers (Groq, with drop-in replacement for OpenAI, Anthropic, etc.)

### CrewAI — Multi-Agent Fraud Analysis

The Fraud Detection Agent runs a **CrewAI sequential crew** — two AI agents that work together in a pipeline:

| Role | Responsibility | 
|------|---------------|
| **Fraud Signal Analyst** | Objectively interprets raw fraud signals (velocity, geography, account age, email) |
| **Risk Adjudicator** | Receives the analyst's interpretation and makes a final decision: `APPROVE` / `HOLD` / `REJECT` |

```python
crew = Crew(
    agents=[analyst, adjudicator],
    tasks=[analyze, adjudicate],
    process=Process.sequential,
)
result = crew.kickoff()  # Two agents debate → one decision
```

This sequential design mirrors real-world fraud operations where an analyst prepares evidence and a senior reviewer makes the call.

### RAG (Retrieval-Augmented Generation) — Grounded Support

The Support Agent uses **ChromaDB** as a vector store, loaded with actual refund policy documents. When a customer asks about returns or refunds, the agent:

1. **Embeds** the query using sentence-transformers
2. **Searches** ChromaDB for the top-3 most relevant policy chunks
3. **Grounds** the LLM response in the retrieved policy text

```python
vectorstore = load_vectorstore()  # ChromaDB with policy embeddings
docs = vectorstore.similarity_search(query, k=3)
# LLM generates answer grounded in retrieved policy chunks
```

This prevents hallucination — the Support Agent's answers come from actual policy documents, not LLM training data.

### MCP Tool Layer — Decoupled Data Access

All agents share a **unified tool registry** (9 SQLAlchemy-backed functions) abstracted behind `call_tool(name, **kwargs)`. This decoupling means:

- Agents never touch the database directly
- Tools can be swapped without changing agent code
- Adding a new data source = writing one tool function

```python
def call_tool(tool_name: str, **kwargs):
    func = get_tool(tool_name)
    return func(**kwargs)

# Any agent can query any data:
products = call_tool("search_products", query="t-shirt")
order = call_tool("get_order_by_id", order_id="O2001")
```

### EventBus — Agent-to-Agent Collaboration

The **in-process pub/sub EventBus** enables decoupled multi-agent workflows without direct dependencies. When an order is placed, a single event triggers three autonomous handlers:

```python
event_bus.emit("order.created", {
    "order_id": "O2042", "customer_email": "..."
})
# Auto-triggers:
# ─► Fraud Agent runs CrewAI analysis
# ─► Inventory Agent deducts stock
# ─► Stock Alert if threshold exceeded
# ─► Order status updated to confirmed
```

Each handler runs in its own context with its own database session — failures in one don't block others.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Groq API key ([free tier](https://console.groq.com))
- Docker (optional)

### Option 1: Docker
```bash
docker compose -f infrastructure/docker-compose.yml up
```
Open **http://localhost:3000** (frontend) or **http://localhost:8501** (Streamlit).

### Option 2: Manual
```bash
# Clone
git clone https://github.com/yourusername/commerceos-ai.git
cd commerceos-ai

# Backend
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash)
pip install -r requirements.txt
cp .env.example .env            # Add your GROQ_API_KEY
python scripts/seed.py
python rag/vectorstore_setup.py # First time only
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** 🎉

---

## 🧪 Testing & Quality

```bash
# Run all tests with coverage
pytest tests/ -v --cov=commerceos --cov-report=term

# Lint check
ruff check .

# Expected: 33+ tests passing, 80%+ coverage
```

| Metric | Status |
|--------|--------|
| Tests | ✅ 33 passing |
| Linting | ✅ Ruff clean (108 issues fixed) |
| Coverage | ✅ 80%+ |
| Type Safety | ✅ Pydantic + TypedDict |

---

## 🏗️ Project Structure

```
commerceos-ai/
│
├── commerceos/                     # 🧠 Core Engine
│   ├── agents/                     # 5 AI Agents (BaseAgent pattern)
│   │   ├── base.py                 # Abstract base + AgentResult
│   │   ├── registry.py             # Self-registering routing
│   │   └── [support, inventory, fraud, order, pricing]_agent.py
│   ├── orchestration/              # 🔄 Supervisor & Events
│   │   ├── supervisor.py           # LangGraph StateGraph + MemorySaver
│   │   ├── event_bus.py           # Pub/sub collaboration layer
│   │   └── workflows.py           # Event-driven workflow definitions
│   ├── mcp/                        # 🔧 Tool Layer
│   │   ├── tools.py               # 9 DB-backed tools
│   │   └── registry.py            # Tool discovery
│   ├── database/                   # 💾 Persistence
│   │   ├── models.py              # 7 SQLAlchemy ORM models
│   │   ├── connection.py          # Session factory
│   │   └── seed.py                # CSV → SQLite seeder
│   └── observability/             # 📊 Observability
│       ├── logger.py              # Structured JSON logging
│       └── activity_tracker.py    # Every action → AgentLog table
│
├── backend/                        # 🌐 FastAPI REST API
├── frontend/                       # 🎨 Next.js Storefront
├── pages/                          # 🖥️ Streamlit pages (legacy)
├── ui/                             # Shared UI components & assets
├── infrastructure/                 # 🐳 Docker
├── tests/                          # 🧪 33 tests
└── data/                           # 📦 CSV seeds
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Languages** | Python 3.13, TypeScript |
| **AI Orchestration** | LangGraph (StateGraph + MemorySaver) |
| **Agent Framework** | LangChain, CrewAI (2-role sequential), ChromaDB RAG |
| **LLM Provider** | Groq API (llama-3.3-70b) |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic |
| **Frontend** | Next.js 14, React 18, Tailwind CSS |
| **Database** | SQLite (dev) / PostgreSQL-ready |
| **Infrastructure** | Docker, docker-compose |
| **CI/CD** | GitHub Actions (lint + test + coverage) |
| **Quality** | Ruff (linting), pytest-cov (coverage) |

---

## 🔒 Security

- **API Keys** stored in `.env` (gitignored) — never committed
- **Admin Access** configured via `ADMIN_PASSWORD` env var — no hardcoded defaults
- **No PII** — seed data uses fictional customers
- **Dependencies** auditable via `pip-audit`

---

## 📄 License

MIT

---

<div align="center">
  <p><strong>Built with LangGraph, CrewAI, and FastAPI</strong></p>
  <p>
    <a href="#-overview">Overview</a> ·
    <a href="#-system-architecture">Architecture</a> ·
    <a href="#-the-five-agents">Agents</a> ·
    <a href="#-quick-start">Quick Start</a>
  </p>
  <br/>
</div>
