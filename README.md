# CommerceOS AI 🛍️

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red?logo=streamlit&logoColor=white)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4-green)]()
[![CrewAI](https://img.shields.io/badge/CrewAI-0.105-orange)]()
[![Ruff](https://img.shields.io/badge/Ruff-0.9-purple)]()
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/Coverage-80%25-yellowgreen)]()

> **Autonomous multi-agent e-commerce operations system** — Five AI agents collaborate to run a full e-commerce storefront. Order management, fraud detection, inventory control, customer support, and dynamic pricing — all powered by a LangGraph supervisor, CrewAI analysis pipeline, and event-driven agent collaboration.

---

## ✨ What Makes This Different

Most e-commerce demos are CRUD apps with a chatbot bolted on. CommerceOS AI is different:

| Feature | What It Means |
|---------|---------------|
| **Agent-to-Agent Collaboration** | Place an order → fraud check + inventory deduction + stock alerts fire automatically via EventBus, without a human in the loop |
| **CrewAI Fraud Pipeline** | Two AI agents (Signal Analyst → Risk Adjudicator) debate each flagged order before making a decision |
| **LangGraph Supervisor** | Routes queries to the right specialist agent — no hardcoded if/else chains, adding a new agent is one file + one registry line |
| **RAG-Grounded Support** | Support Agent answers from actual policy documents via ChromaDB, not LLM hallucination |
| **Full Observability** | Every agent action is logged to the AgentLog table and visible in the Admin Dashboard |

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│              STREAMLIT STOREFRONT                 │
│  Browse → Cart → Checkout → AI Assistant          │
│  Order History → Admin Dashboard                  │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│            LANGGRAPH SUPERVISOR                    │
│     AgentRegistry routing + MemorySaver            │
│     (keyword pre-check → LLM fallback → 5 agents)  │
└───┬──────┬──────┬──────┬──────┬───────────────────┘
    │      │      │      │      │
┌───▼──┐ ┌─▼──┐ ┌─▼──┐ ┌▼───┐ ┌▼──────┐
│Supp. │ │Inv.│ │Frau│ │Order│ │Pricing│
│(RAG) │ │LLM │ │Crew│ │LLM │ │LLM    │
└──────┘ └────┘ └────┘ └────┘ └───────┘
    │      │      │      │      │
┌───▼──────▼──────▼──────▼──────▼──────────────┐
│           MCP TOOL LAYER (SQLAlchemy)           │
│  Products │ Orders │ Customers │ AgentLog       │
└──────────────────────┬─────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────┐
│              EVENT BUS + WORKFLOWS               │
│   order.created → fraud check → inventory ded.  │
│   → stock alert → status update → AgentLog       │
└──────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Docker (recommended)

```bash
docker compose -f infrastructure/docker-compose.yml up
```

Open **http://localhost:8501** in your browser. The database auto-seeds on first run.

### Option 2: Manual

```bash
# 1. Clone and enter
git clone https://github.com/yourusername/commerceos-ai.git
cd commerceos-ai

# 2. Set up environment
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash)
# source venv/bin/activate      # macOS/Linux
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env — add your Groq API key and admin password

# 4. Seed the database
python scripts/seed.py

# 5. (First time only) Build the RAG vectorstore
python rag/vectorstore_setup.py

# 6. Launch
streamlit run app.py
```

## 🤖 Agents

| Agent | Framework | What It Does | When To Ask |
|-------|-----------|-------------|-------------|
| **Support** | LangChain + RAG (ChromaDB) | Policy questions, order lookups, cross-agent queries | "Can I return a damaged item?" |
| **Inventory** | LangChain | Stock checks, low-stock alerts, reorder monitoring | "Do you have white t-shirts in stock?" |
| **Fraud** | CrewAI (2-role pipeline) | Signal Analyst → Risk Adjudicator sequential analysis | "Check order O2004 for fraud" |
| **Order** | LangChain | Order lifecycle, tracking numbers, cancellations | "Where is my order O2001?" |
| **Pricing** | LangChain | Sale suggestions, slow-moving inventory analysis | "Any items on sale right now?" |

## ⚡ Event-Driven Workflows

```
┌──────────────┐
│  Order       │
│  Placed      │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Fraud Agent  │────▶│ Inventory        │────▶│ Stock Alert      │
│ (CrewAI      │     │ Deducted         │     │ (if low stock)   │
│  analysis)   │     │                  │     │                  │
└──────────────┘     └──────────────────┘     └──────────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Order Status │────▶│ AgentLog         │────▶│ Admin Dashboard  │
│ → confirmed  │     │ (all steps)      │     │ (displays all)   │
└──────────────┘     └──────────────────┘     └──────────────────┘
```

## 📊 Pages

| Page | Purpose |
|------|---------|
| **Home** 🏠 | Product grid with category filters, sale badges, search |
| **Cart & Checkout** 🛒 | Full cart with quantity adjustment, checkout form, event-triggered workflows |
| **AI Assistant** 🤖 | Chat interface to all 5 agents with example buttons and admin mode |
| **Order History** 📋 | Look up orders by email, view status and fraud results |
| **Admin Dashboard** ⚙️ | Operations control: fraud alerts, stock overview, agent activity log, quick actions |

## 🧪 Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=commerceos

# Run specific test file
pytest tests/test_agents.py -v
```

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Runtime** | Python 3.13, Streamlit |
| **AI Orchestration** | LangGraph (StateGraph + MemorySaver) |
| **Agent Framework** | LangChain, CrewAI (2-role sequential), ChromaDB RAG |
| **LLM Provider** | Groq API (free tier) — swap any OpenAI-compatible endpoint |
| **Database** | SQLAlchemy ORM + SQLite (dev) / PostgreSQL-ready |
| **Infrastructure** | Docker, docker-compose |
| **CI/CD** | GitHub Actions (lint + test + coverage) |
| **Quality** | ruff (linting), pytest-cov (coverage) |

## 📁 Project Structure

```
commerceos-ai/
├── commerceos/                    # 🧠 Engine package
│   ├── agents/                    # 5 AI agents (BaseAgent pattern)
│   │   ├── base.py                # Abstract base + AgentResult
│   │   ├── registry.py            # Self-registering agent registry
│   │   ├── support_agent.py       # RAG-based customer support
│   │   ├── inventory_agent.py     # Stock management
│   │   ├── fraud_agent.py         # CrewAI 2-role fraud pipeline
│   │   ├── order_agent.py         # Order lifecycle
│   │   └── pricing_agent.py       # Dynamic pricing
│   ├── orchestration/             # 🔄 Supervisor + events
│   │   ├── supervisor.py          # LangGraph StateGraph
│   │   ├── event_bus.py           # Pub/sub event system
│   │   └── workflows.py           # Event-driven workflows
│   ├── mcp/                       # 🔧 MCP tool layer
│   │   ├── tools.py               # 9 DB-backed tools
│   │   └── registry.py            # Tool registry
│   ├── database/                  # 💾 Persistence
│   │   ├── models.py              # 7 SQLAlchemy models
│   │   ├── connection.py          # Session management
│   │   └── seed.py                # CSV seeding
│   └── observability/             # 📊 Monitoring
│       ├── logger.py              # Structured JSON logging
│       └── activity_tracker.py    # AgentLog table writer
├── pages/                         # 🖥️ Streamlit views
│   ├── Cart.py                    # Cart + event emission
│   ├── AI_Assistant.py            # 5-agent chat panel
│   ├── order_history.py           # Email lookup
│   └── admin_dashboard.py         # Ops dashboard
├── ui/                            # 🎨 Shared UI
│   ├── components.py              # Reusable widgets
│   ├── styling.py                 # Brand CSS
│   └── assets/images/             # 20 SVG product images
├── rag/                           # 📚 RAG vectorstore
│   └── vectorstore_setup.py       # ChromaDB setup
├── infrastructure/                # 🐳 Docker
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── entrypoint.sh
├── tests/                         # 🧪 Test suite
│   ├── test_agents.py             # Agent routing tests
│   ├── test_tools.py              # MCP tool tests
│   └── test_workflows.py          # Integration tests
├── data/                          # 📦 Data files
│   ├── products.csv               # 20 products
│   ├── orders.csv                 # 15 orders
│   └── commerceos.db              # SQLite DB (runtime)
├── docs/                          # 📝 Documentation
│   └── superpowers/specs/         # Design specs
└── backend/                       # 🌐 FastAPI REST API
    └── main.py                    # API endpoints
```

## 🔒 Security

- **API keys** go in `.env` (gitignored) — never committed to the repository
- **Admin password** configured via `ADMIN_PASSWORD` env variable — no hardcoded defaults
- **No real PII** — seed data uses fictional customer information
- Copy `.env.example` to `.env` and fill in your values before running

## 🗺️ Roadmap

- [x] 5 specialist agents with LangGraph routing
- [x] Event-driven workflows (order → fraud → inventory)
- [x] CrewAI fraud analysis pipeline
- [x] Full Streamlit storefront with checkout
- [x] Docker deployment
- [x] CI/CD pipeline with linting and coverage
- [ ] Real MCP server transport (SSE-based)
- [ ] ML-based fraud scoring on top of rule-based signals
- [ ] Cross-agent shared memory across sessions
- [ ] PostgreSQL support for horizontal scaling

## 📄 License

MIT
