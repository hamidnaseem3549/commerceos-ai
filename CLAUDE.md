# CommerceOS AI

## Overview
An **autonomous multi-agent e-commerce operations system** with a live Streamlit storefront ("Urban Thread Co."). A LangGraph Supervisor routes user queries to 5 specialist agents via AgentRegistry. Event-driven workflows enable automatic fraud checks, inventory deduction, and alerting when orders are placed. SQLite + SQLAlchemy provides persistent storage.

## Quick Start
```bash
# Option 1: Docker (recommended)
docker compose -f infrastructure/docker-compose.yml up

# Option 2: Manual
source venv/Scripts/activate  # Git Bash
pip install -r requirements.txt
python scripts/seed.py
streamlit run app.py
```

## Architecture

```
Streamlit Storefront (Browse | Cart | AI Assistant | Admin)
        │
        ▼
LANGGRAPH SUPERVISOR (AgentRegistry routing + MemorySaver)
  keyword pre-check → LLM fallback → 5 agents
        │
   ┌────┼────┬────┬────┐
   ▼    ▼    ▼    ▼    ▼
Support Inventory Fraud  Order  Pricing
(RAG)   (LLM)  (CrewAI) (LLM)  (LLM)
   │    │      │        │      │
   └────┴──────┴────────┴──────┘
        │
        ▼
MCP TOOL LAYER (SQLAlchemy ORM)
  Products | Orders | Customers | AgentLog
        │
        ▼
EVENT BUS (auto-triggered workflows)
  order.created → fraud check + inventory deduct + alert
```

## Project Structure

```
commerceos-ai/
├── commerceos/                      # Engine package (all business logic)
│   ├── config.py                    # Central config (env-based)
│   ├── agents/                      # 5 pluggable agents (BaseAgent pattern)
│   │   ├── base.py                  # Abstract BaseAgent
│   │   ├── registry.py              # AgentRegistry (discoverable routing)
│   │   ├── support_agent.py         # RAG (ChromaDB) + order lookups
│   │   ├── inventory_agent.py       # Stock queries + auto-alerts
│   │   ├── fraud_agent.py           # CrewAI 2-role (Analyst → Adjudicator)
│   │   ├── order_agent.py           # Order lifecycle, tracking, cancellations
│   │   └── pricing_agent.py         # Dynamic pricing, sales, slow-mover analysis
│   ├── orchestration/               # Supervisor + event system
│   │   ├── supervisor.py            # LangGraph StateGraph (AgentRegistry routing)
│   │   ├── event_bus.py             # Pub/sub for agent collaboration
│   │   └── workflows.py             # Event-driven workflow definitions
│   ├── mcp/                         # MCP Tool Layer (shared data access)
│   │   └── tools.py                 # 9 DB-backed tool functions
│   ├── database/                    # Persistence layer
│   │   ├── models.py                # 7 SQLAlchemy ORM models
│   │   ├── connection.py            # Engine + session factory
│   │   └── seed.py                  # CSV → SQLite seeding
│   └── observability/               # Monitoring
│       ├── logger.py                # Structured JSON logging
│       └── activity_tracker.py      # Every agent action → AgentLog table
├── pages/                           # Streamlit views (5 pages)
│   ├── Cart.py                      # Cart + checkout with event emission
│   ├── AI_Assistant.py              # AI chat panel (all 5 agents)
│   ├── order_history.py             # Customer order lookup by email
│   └── admin_dashboard.py           # Ops panel: fraud alerts, stock, agent log
├── rag/                             # RAG subsystem
│   └── vectorstore_setup.py         # ChromaDB from refund_policy.txt
├── ui/                              # Shared UI components + assets
│   ├── components.py                # Reusable Streamlit widgets
│   ├── styling.py                   # Brand CSS injection
│   └── assets/images/               # 20 SVG product placeholders
├── infrastructure/                  # Deployment artifacts
│   ├── Dockerfile, docker-compose.yml, entrypoint.sh
├── tests/                           # 20 tests (tools, agents, workflows)
├── data/                            # CSV seeds + runtime commerceos.db
└── scripts/seed.py                  # CLI: python scripts/seed.py
```

## Key Technical Details

### Agent Registry Routing
- Agents self-register via `AgentRegistry.register(agent)` in `commerceos/agents/__init__.py`
- `AgentRegistry.route(query)` uses keyword matching (longest match wins)
- Supervisor falls back to LLM (ChatGroq) for ambiguous queries
- No hardcoded routing — adding an agent = 1 file + 1 registry line

### Event-Driven Workflows
- `EventBus` in `commerceos/orchestration/event_bus.py`
- `order.created` event auto-triggers: fraud check → inventory deduct → stock alert → status update
- Events fire after DB commit so handlers get their own session
- All actions recorded in `AgentLog` table

### Database
- SQLite via SQLAlchemy ORM (7 tables: Product, Customer, Order, OrderItem, AgentLog, FraudSignal, Alert)
- Fresh session per call (`sessionmaker`, not `scoped_session`)
- Seed from CSVs: `python scripts/seed.py`

### AI Assistant Integration
- All 5 agents accessible via chat: Support, Inventory, Fraud (CrewAI), Order, Pricing
- 5 example buttons for quick testing
- Admin mode toggle shows internal ops alerts
- Session history via LangGraph MemorySaver

### Admin Dashboard
- Password-gated (default: admin123)
- Fraud alerts, low stock overview, agent activity feed, system stats
- Quick actions: Run fraud sweep, check stock, analyze pricing

### MCP Tool Layer
- 9 tool functions: `get_all_products`, `search_products`, `get_low_stock_products`, `get_product_by_id`, `get_order_by_id`, `get_orders_by_email`, `get_fraud_signals`, `get_all_flagged_orders`, `append_order`
- All agents call `call_tool(name, **kwargs)` — decoupled from storage

## Framework Choices
- **LangGraph**: orchestration spine with MemorySaver checkpointer
- **LangChain + RAG**: grounds Support Agent in actual policy text via ChromaDB
- **CrewAI**: 2-role sequential crew for fraud analysis (Signal Analyst → Risk Adjudicator)
- **SQLAlchemy ORM**: database access shared across all agents

## Important Gotchas
- CrewAI's `cache_breakpoint` field is monkey-patched to a no-op — removing this causes Groq API errors
- Vectorstore must be built (`python rag/vectorstore_setup.py`) before support agent works
- `.env` is gitignored — never commit real API keys
- `data/chroma_store/` is gitignored — must be rebuilt on fresh clones
- Test suite uses real DB (not in-memory) — run `python scripts/seed.py` before tests
