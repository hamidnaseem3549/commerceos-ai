# CommerceOS AI 🛍️

[![Python](https://img.shields.io/badge/Python-3.13-blue)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4-green)]()
[![CrewAI](https://img.shields.io/badge/CrewAI-0.105-orange)]()

**Autonomous multi-agent e-commerce operations system** — five AI agents collaborate to run a full e-commerce storefront. Order management, fraud detection, inventory control, customer support, and dynamic pricing — all powered by a LangGraph supervisor, CrewAI analysis pipeline, and event-driven agent collaboration.

## ✨ Features

- **5 Specialist Agents** — Support (RAG), Inventory, Fraud (CrewAI 2-role), Order Management, Pricing
- **Event-Driven Collaboration** — Place an order → auto-triggers fraud analysis + inventory deduction + stock alerts
- **Persistent Database** — SQLite via SQLAlchemy ORM (data survives restarts)
- **Admin Dashboard** — Real-time fraud alerts, stock overview, agent activity log, quick actions
- **Professional Storefront** — Product images, category filters, sale badges, full cart checkout
- **One-Command Deploy** — `docker compose up` boots the full stack
- **Observability** — Every agent action is logged and visible in the admin panel

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              STREAMLIT STOREFRONT                │
│  Browse → Cart → Checkout → AI Assistant        │
│  Order History → Admin Dashboard                │
└───────────────────────┬─────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────┐
│            LANGGRAPH SUPERVISOR                  │
│     AgentRegistry routing + MemorySaver          │
└───┬──────┬──────┬──────┬──────┬─────────────────┘
    │      │      │      │      │
┌───▼──┐ ┌─▼──┐ ┌─▼──┐ ┌▼───┐ ┌▼──────┐
│Supp. │ │Inv.│ │Frau│ │Order│ │Pricing│
│(RAG) │ │LLM │ │Crew│ │LLM │ │LLM    │
└──────┘ └────┘ └────┘ └────┘ └───────┘
    │      │      │      │      │
┌───▼──────▼──────▼──────▼──────▼──────────────┐
│           MCP TOOL LAYER (SQLAlchemy)          │
│  Products │ Orders │ Customers │ AgentLog      │
└───────────────────────┬────────────────────────┘
                        │
┌───────────────────────▼────────────────────────┐
│              EVENT BUS + WORKFLOWS              │
│   order.created → fraud check + inventory ded. │
└─────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# Option 1: Docker (recommended — one command)
docker compose -f infrastructure/docker-compose.yml up

# Option 2: Manual
python -m venv venv
source venv/Scripts/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python scripts/seed.py
streamlit run app.py
```

## 🤖 Agents

| Agent | Framework | What It Does |
|---|---|---|
| **Support** | LangChain + RAG | Policy questions, order lookups, cross-agent queries |
| **Inventory** | LangChain | Stock checks, low-stock alerts, reorder monitoring |
| **Fraud** | CrewAI (2-role) | Signal Analyst → Risk Adjudicator sequential pipeline |
| **Order** | LangChain | Order lifecycle, tracking numbers, cancellations |
| **Pricing** | LangChain | Sale suggestions, slow-moving inventory analysis |

## ⚡ Event-Driven Workflows

```
Order Placed
  → Fraud Agent auto-checks (CrewAI analysis)
  → Inventory deducted from stock
  → Low-stock alert if threshold hit
  → Order status: pending → confirmed
  → AgentLog records every step
  → Admin Dashboard displays all results
```

## 📊 Pages

| Page | Purpose |
|---|---|
| **Home** | Product grid with category filters, sale badges, search |
| **Cart & Checkout** | Full cart, quantity adjustment, order summary, checkout |
| **AI Assistant** | Chat interface to all 5 agents with example buttons |
| **Order History** | Look up orders by email, view status and fraud results |
| **Admin Dashboard** | Operations control: fraud alerts, stock overview, agent log, quick actions |

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🛠️ Tech Stack

- **Runtime:** Python 3.13, Streamlit
- **Agents:** LangGraph, LangChain (+ RAG), CrewAI
- **Database:** SQLAlchemy ORM + SQLite
- **LLM Provider:** Groq API (free tier)
- **Infrastructure:** Docker, docker-compose
- **CI:** GitHub Actions (pytest on push)

## 📁 Project Structure

```
commerceos-ai/
├── commerceos/              # Engine package (all business logic)
│   ├── agents/              # 5 pluggable AI agents (BaseAgent pattern)
│   ├── orchestration/       # LangGraph supervisor + EventBus + workflows
│   ├── mcp/                 # MCP tool layer (data access via SQLAlchemy)
│   ├── database/            # SQLAlchemy models + connection + seeding
│   └── observability/       # Structured logging + activity tracking
├── pages/                   # Streamlit page views (thin — no business logic)
├── ui/                      # Shared UI components, styling, product images
├── infrastructure/          # Docker deployment
├── tests/                   # Test suite (15+ tests)
├── rag/                     # RAG vectorstore for support agent
├── data/                    # CSV seeds + runtime SQLite DB
├── scripts/                 # CLI utilities
├── docs/                    # Architecture docs + design specs
└── .env.example             # API key template (copy to .env)
```

## 🔒 Important Notes

- Get a free Groq API key at https://console.groq.com
- Copy `.env.example` to `.env` and add your key
- Run `python scripts/seed.py` once to populate the database from CSVs
- The admin dashboard uses password `admin123` (change in production)
- All data is stored in `data/commerceos.db` — delete to reset

## 🗺️ Roadmap

- Real MCP server transport (SSE-based)
- ML-based fraud scoring on top of rule-based signals
- Cross-agent shared memory across sessions
- PostgreSQL support for horizontal scaling
