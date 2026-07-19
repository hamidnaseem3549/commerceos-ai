# CommerceOS AI — MVP Design Specification

**Date:** 2026-07-19
**Status:** Draft | **Version:** 1.0
**Author:** CommerceOS AI Design Team

---

## 1. Overview & Vision

CommerceOS AI is an **autonomous multi-agent e-commerce operations system**. It transforms a basic Streamlit storefront ("Urban Thread Co.") into a production-feeling agentic commerce platform where AI agents collaborate, react to events, and manage the full order lifecycle autonomously.

**The core philosophy:** Agents should act, not just answer. When an order is placed, the system should independently run fraud checks, update inventory, log all activity, and generate alerts — without a human asking for each step.

---

## 2. Guiding Principles

| Principle | Application |
|---|---|
| **Domain-driven** | Code organized by business domain (agents, orchestration, mcp, database), not by technical layer |
| **Pluggable agents** | Adding a new agent = 1 file + 1 registry entry. No supervisor graph changes |
| **Event-driven collaboration** | Agents communicate through an event bus — no direct imports between agents |
| **Observable by default** | Every agent action is logged, timestamped, and visible in the admin dashboard |
| **Deployable in one command** | `docker compose up` boots the full stack with DB migrations auto-applied |
| **Testable** | All agents accept mockable dependencies; tests use in-memory databases |

---

## 3. Project Structure (Professional Layout)

```
commerceos-ai/
│
├── app.py                                # Thin Streamlit entrypoint — pages/ does the rest
│
├── pages/                                # Streamlit-page views (thin — no business logic)
│   ├── cart.py                           # Cart view + checkout form
│   ├── ai_assistant.py                   # AI chat panel
│   ├── order_history.py                  # Customer order history (NEW)
│   └── admin_dashboard.py                # Ops dashboard with metrics (NEW)
│
├── commerceos/                           # ⬅ ENGINE LAYER — all business logic
│   ├── __init__.py
│   │
│   ├── config.py                         # Single source of truth for all settings
│   │                                     # Reads from env vars, .env, provides defaults
│   │
│   ├── agents/                           # Agent definitions — pluggable, self-contained
│   │   ├── __init__.py
│   │   ├── base.py                       # Abstract BaseAgent with shared interface
│   │   ├── registry.py                   # AgentRegistry — discover, route, list agents
│   │   ├── support_agent.py              # RAG-enhanced customer support (EXISTING, refactored)
│   │   ├── inventory_agent.py            # Stock queries + auto-alerts (EXISTING, refactored)
│   │   ├── fraud_agent.py                # CrewAI 2-role fraud analysis (EXISTING, refactored)
│   │   ├── order_agent.py                # Order lifecycle management (NEW)
│   │   └── pricing_agent.py              # Dynamic pricing suggestions (NEW)
│   │
│   ├── orchestration/                    # Supervisor + event system
│   │   ├── __init__.py
│   │   ├── supervisor.py                 # LangGraph StateGraph (moved from root)
│   │   ├── event_bus.py                  # EventBus: pub/sub dispatch for auto-triggers
│   │   └── workflows.py                  # Event-driven workflow definitions
│   │
│   ├── mcp/                              # MCP Tool Layer — shared data access
│   │   ├── __init__.py
│   │   ├── registry.py                   # ToolRegistry: name → callable mapping
│   │   └── tools.py                      # All MCP tool functions (refactored for DB)
│   │
│   ├── database/                         # Persistence layer
│   │   ├── __init__.py
│   │   ├── models.py                     # SQLAlchemy ORM: Product, Order, Customer, etc.
│   │   ├── connection.py                 # Engine + SessionLocal factory
│   │   └── seed.py                       # Seed from existing CSVs into SQLite
│   │
│   └── observability/                    # Monitoring
│       ├── __init__.py
│       ├── logger.py                     # Structured logging (stdout JSON)
│       └── activity_tracker.py           # Records every agent action → AgentLog table
│
├── rag/                                  # RAG subsystem (standalone, minimal surface)
│   ├── __init__.py
│   └── vectorstore.py                    # load_vectorstore(), build_vectorstore()
│
├── ui/                                   # Shared UI components
│   ├── __init__.py
│   ├── components.py                     # Reusable Streamlit widgets (cards, badges, etc.)
│   ├── styling.py                        # Brand CSS injection (moved from utils/)
│   └── assets/images/                    # Product placeholder images
│       └── gen_placeholders.py           # Script to generate placeholder product images
│
├── infrastructure/                       # Deployment artifacts
│   ├── Dockerfile                        # Production image
│   ├── docker-compose.yml                # Full stack: app + init + volume
│   ├── entrypoint.sh                     # Container startup: migrations → seed → launch
│   └── alembic/                          # Database migration management
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
│
├── tests/                                # Test suite
│   ├── conftest.py                       # Fixtures: test DB, mock tools, test agent
│   ├── test_tools.py                     # MCP tool unit tests
│   ├── test_agents.py                    # Agent unit tests
│   └── test_workflows.py                 # Integration tests for event workflows
│
├── scripts/                              # Developer utilities
│   ├── setup.sh                          # One-time dev environment setup
│   └── seed.py                           # CLI: seed DB from CSVs
│
├── docs/                                 # Project documentation
│   └── architecture.md                   # Mermaid architecture diagram
│
├── data/                                 # Runtime data (gitignored except originals)
│   ├── products.csv                      # Original product catalog (source of truth for seed)
│   ├── orders.csv                        # Original order history (source of truth for seed)
│   ├── refund_policy.txt                 # Store policy for RAG
│   ├── commerceos.db                     # SQLite database (auto-generated, GITIGNORE)
│   └── chroma_store/                     # Vector database (auto-generated, GITIGNORE)
│
├── .env.example                          # Key template with NO real values
├── .gitignore                            # Updated for new paths
├── pyproject.toml                        # Project metadata, test config, dependencies
├── requirements.txt                      # Python package requirements
├── CLAUDE.md                             # Project guide for AI assistants
└── README.md                             # Professional README with diagrams
```

---

## 4. Database Schema (SQLAlchemy ORM)

### 4.1 Entity-Relationship Design

```
┌─────────────┐       ┌─────────────────┐       ┌──────────────┐
│  Customer    │       │     Order       │       │   Product    │
├─────────────┤       ├─────────────────┤       ├──────────────┤
│ id (PK)     │◄──┐   │ id (PK)         │   ┌──►│ id (PK)      │
│ name        │   └───│ customer_id (FK)│   │   │ name         │
│ email       │       │ status          │   │   │ category     │
│ acct_age_d  │       │ total_amount    │   │   │ price        │
│ created_at  │       │ tracking_num    │   │   │ stock_qty    │
│ total_orders│       │ created_at      │   │   │ reorder_thr  │
│ total_spent │       │ updated_at      │   │   │ image_url    │
└─────────────┘       │ shipping_addr   │   │   │ is_on_sale   │
                      │ billing_addr    │   │   │ sale_price   │
                      │ payment_method  │   │   └──────────────┘
                      └────────┬────────┘           ▲
                               │                    │
                      ┌────────▼────────┐           │
                      │   OrderItem     │           │
                      ├─────────────────┤           │
                      │ id (PK)         │───────────┘
                      │ order_id (FK)   │
                      │ product_id (FK) │
                      │ quantity        │
                      │ unit_price      │
                      └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   AgentLog      │  │   FraudSignal   │  │   Alert         │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id (PK)         │  │ id (PK)         │  │ id (PK)         │
│ agent_name      │  │ order_id (FK)   │  │ type            │
│ action          │  │ signal_type     │  │ severity        │
│ detail          │  │ triggered       │  │ message         │
│ level           │  │ checked_at      │  │ resolved        │
│ timestamp       │  │ analyst_output  │  │ created_at      │
│ query_id        │  │ decision        │  │ source_agent    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 4.2 Table Definitions

#### Product
| Column | Type | Notes |
|---|---|---|
| id | String (PK) | e.g., P1001 |
| name | String | Product name |
| category | String | Apparel, Electronics, Accessories, etc. |
| price | Float | Base price |
| stock_quantity | Integer | Current stock |
| reorder_threshold | Integer | Min stock before alert |
| image_url | String | Path to placeholder image |
| is_on_sale | Boolean | Set by Pricing Agent |
| sale_price | Float, nullable | Discounted price |
| created_at | DateTime | Auto-set |

#### Customer
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | Auto-increment |
| name | String | |
| email | String (unique) | |
| account_age_days | Integer | Days since registration |
| total_orders | Integer | Denormalized counter |
| total_spent | Float | Denormalized sum |
| created_at | DateTime | Auto-set |

#### Order
| Column | Type | Notes |
|---|---|---|
| id | String (PK) | e.g., O2001 |
| customer_id | Integer (FK → Customer) | |
| status | String | pending → confirmed → processing → shipped → delivered → cancelled |
| total_amount | Float | |
| tracking_number | String, nullable | Generated by Order Agent |
| shipping_address | String | |
| billing_address | String | |
| payment_method | String | |
| notes | Text, nullable | Agent-generated notes |
| created_at | DateTime | |
| updated_at | DateTime | Auto-updated |

#### OrderItem
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| order_id | String (FK → Order) | |
| product_id | String (FK → Product) | |
| quantity | Integer | |
| unit_price | Float | Price at time of order |

#### AgentLog
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| agent_name | String | Which agent acted |
| action | String | Action verb (e.g., "query", "fraud_check", "stock_alert") |
| detail | Text | Human-readable description |
| level | String | INFO, WARNING, ERROR |
| query_id | String, nullable | Correlates actions to a user query |
| timestamp | DateTime | Auto-set |

#### FraudSignal
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| order_id | String (FK → Order) | |
| signal_type | String | velocity, country_mismatch, new_account, disposable_email |
| triggered | Boolean | |
| checked_at | DateTime | |
| analyst_output | Text, nullable | CrewAI Signal Analyst's interpretation |
| decision | String, nullable | APPROVE / HOLD / REJECT |

#### Alert
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| type | String | low_stock, fraud_flag, order_anomaly, system |
| severity | String | LOW, MEDIUM, HIGH, CRITICAL |
| message | Text | |
| resolved | Boolean | Default false |
| source_agent | String | Which agent raised this |
| created_at | DateTime | |

### 4.3 Seed Strategy

The existing `products.csv` and `orders.csv` are the seed sources. On first boot (or `scripts/seed.py`):
1. Products table is populated from `data/products.csv`
2. Orders table is populated from `data/orders.csv` — each order auto-creates a Customer entry (if not exists) and OrderItem entries
3. AgentLog, FraudSignal, Alert tables start empty (populated at runtime)

---

## 5. Agent Architecture

### 5.1 Base Agent Contract

All agents inherit from `BaseAgent`:

```python
class BaseAgent(ABC):
    name: str                      # Agent identifier
    description: str               # What this agent does
    
    @abstractmethod
    def run(self, query: str) -> AgentResult:
        """Execute agent logic for a user query."""
        ...

class AgentResult(TypedDict):
    answer: str                    # Customer-facing response
    agent: str                     # Agent name
    ops_alert: str                 # Internal alert (empty if none)
    context_used: str              # What data was used
    actions: list[dict]            # Recorded actions for AgentLog
```

### 5.2 Agent Registry

`AgentRegistry` is a singleton that maps agent names to instances. The supervisor queries the registry to find the right agent — no hardcoded routing.

```python
class AgentRegistry:
    agents: dict[str, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent: BaseAgent): ...
    @classmethod
    def get(cls, name: str) -> BaseAgent: ...
    @classmethod
    def list(cls) -> list[str]: ...
    @classmethod
    def route(cls, query: str) -> str: ...  # keyword + LLM routing
```

### 5.3 Agent Catalog

#### Support Agent (Existing — Refactored)
- **Framework:** LangChain (ChatGroq) + RAG (ChromaDB)
- **Capabilities:** Policy questions via RAG, order lookups via DB, cross-agent inventory queries
- **Refactored:** Uses database models instead of direct CSV reads. Can optionally query Inventory Agent for stock-related questions in a support context

#### Inventory Agent (Existing — Refactored)
- **Framework:** LangChain (ChatGroq)
- **Capabilities:** Product availability, stock checks, category suggestions
- **Refactored:** Uses DB queries instead of CSV. Auto-generated alerts when stock drops below threshold. Can be triggered by `event_bus` after an order is placed
- **Dual output:** Customer-friendly answer + internal ops alert

#### Fraud Agent (Existing — Refactored)
- **Framework:** CrewAI (Signal Analyst → Risk Adjudicator)
- **Capabilities:** Single-order fraud analysis, full-order sweep
- **Refactored:** Results persisted to `FraudSignal` table. Register as an event listener for `order.created` events. Sweep result shown on admin dashboard

#### Order Agent (New)
- **Framework:** LangChain (ChatGroq)
- **Capabilities:**
  - Order status lookup: "Where is my order?"
  - Order cancellation: "Cancel my order"
  - Order tracking: "What's my tracking number?"
  - Order status progression: generates tracking numbers, updates statuses
- **Key behavior:** Acts as the authoritative source for order lifecycle. Other agents query the Order Agent for order state rather than reading the database directly

#### Pricing Agent (New)
- **Framework:** LangChain (ChatGroq) with data analysis
- **Capabilities:**
  - Analyze slow-moving inventory (products with high stock, low sales)
  - Suggest markdown prices
  - Apply sale flags to products
  - Answer pricing questions: "Why is this on sale?", "Any deals right now?"
- **Key behavior:** Runs a background analysis when triggered. Updates `is_on_sale` and `sale_price` on Product records

---

## 6. Event-Driven Architecture

### 6.1 Event Bus

The event bus is an in-process publish/subscribe system. Agents never import each other — they publish events and listen for events.

```python
class EventBus:
    listeners: dict[str, list[Callable]]  # event_type → [handler, handler, ...]
    
    def on(self, event_type: str, handler: Callable): ...
    def emit(self, event_type: str, data: dict): ...
    def remove(self, event_type: str, handler: Callable): ...
```

### 6.2 Events

| Event | Emitted By | Handled By | Purpose |
|---|---|---|---|
| `order.created` | Cart checkout → Order Agent | Fraud Agent, Inventory Agent | Auto-trigger fraud check + inventory update |
| `fraud.analyzed` | Fraud Agent | Admin dashboard (via Alert) | Show fraud result in admin panel |
| `stock.low` | Inventory Agent | Admin dashboard (via Alert) | Alert for reorder |
| `pricing.sale_applied` | Pricing Agent | Storefront (via DB update) | Show sale badges |
| `agent.action` | All agents | Activity Tracker | Log to AgentLog table |

### 6.3 Workflow: Order Placed → Auto Chain

```
1. User submits checkout form
2. Cart page calls commerceos.orchestration.event_bus.emit("order.created", {order_id, customer, items})
3. EventBus dispatches to:
   a. Order Agent handler:       Creates order record (status: pending → confirmed)
                                 Generates tracking number
                                 Logs to AgentLog
   b. Fraud Agent handler:       Runs CrewAI analysis on the new order
                                 Persists result to FraudSignal table
                                 Emits "fraud.analyzed" if HOLD or REJECT
   c. Inventory Agent handler:   Deducts stock for ordered items
                                 Checks reorder thresholds
                                 Emits "stock.low" if any product is below threshold
4. Admin dashboard picks up alerts via AgentLog + Alert queries
```

**Why this matters for portfolio:** This single workflow demonstrates multiple concepts simultaneously — event-driven architecture, agent autonomy, observability, and multi-agent collaboration — in one observable chain.

---

## 7. Supervisor & Routing

The LangGraph supervisor moves from a single `supervisor.py` at root to `commerceos/orchestration/supervisor.py` with improvements:

1. **Agent Registry integration** — routing discovers agents from the registry rather than hardcoded keyword lists
2. **Event-aware state** — GraphState gains an `events` field to track triggered event chains
3. **CrewAI integration** — The Fraud Agent runs its own CrewAI sequential crew (Signal Analyst → Risk Adjudicator) as a standalone call within the fraud graph node
4. **Memory persistence** — MemorySaver checkpointer continues, but conversation history is also backed by the AgentLog table

**Routing Logic (unchanged philosophy, improved implementation):**
- Keyword pre-check (fast path for fraud/inventory)
- LLM fallback (ChatGroq) for ambiguous queries
- New: agents self-register their keywords in the registry

---

## 8. Storefront Enhancements

### 8.1 Product Grid
- **Product images:** 48x48 SVG placeholder images with product initials on brand-colored backgrounds
- **Category filter tabs:** Click buttons to filter by category (All / Apparel / Electronics / Accessories / Home & Living / Footwear / Sports & Fitness)
- **Sale badges:** Orange "SALE" badge with strikethrough original price and sale price shown
- **Stock badges:** Maintain existing green/yellow/red badges

### 8.2 Cart & Checkout
- **Buy all items:** Loop over every item in cart, create OrderItems for each
- **Order summary:** Line-item table with subtotal, estimated tax (8%), and total
- **Post-checkout:** Redirect to order history page with a success message

### 8.3 Order History Page (New)
- Table of all orders with: Order ID, Date, Items, Total, Status, Tracking
- Click an order → detail view showing all items, fraud result, delivery status
- Empty state: "No orders yet. Start shopping!"

### 8.4 Admin Dashboard (New)
**Sections:**
1. **Fraud Alerts** — Table of recent HOLD/REJECT decisions with order ID, risk level, timestamp
2. **Low Stock Alerts** — Cards for each product below reorder threshold
3. **Agent Activity Feed** — Scrollable log of recent agent actions (from AgentLog)
4. **System Stats** — Cards showing: Total Orders, Active Fraud Cases, Low Stock Items, Uptime
5. **Quick Actions** — "Run Fraud Sweep" (button), "Check All Stock" (button)

---

## 9. Infrastructure

### 9.1 Docker

**Dockerfile:**
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -c "from commerceos.database.connection import init_db; init_db()"
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**docker-compose.yml:**
```yaml
services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - commerceos_data:/app/data
    env_file:
      - .env
    command: >
      sh -c "cd /app && 
             python -m commerceos.database.seed &&
             streamlit run app.py --server.port=8501 --server.address=0.0.0.0"

volumes:
  commerceos_data:
```

### 9.2 CI (GitHub Actions)
```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements.txt
      - run: pip install pytest
      - run: python -c "from commerceos.database.connection import init_db; init_db()"
      - run: pytest tests/ -v
```

### 9.3 Alembic Migrations
- `alembic init` configured to use the SQLite URL from config
- Initial migration creates all tables listed in Section 4
- Future schema changes go through `alembic revision --autogenerate`

---

## 10. Testing Strategy

### 10.1 Test Infrastructure
- **conftest.py** provides:
  - `test_db`: In-memory SQLite database for isolated tests
  - `sample_product`, `sample_order`, `sample_customer`: Test data fixtures
  - `mock_llm`: Fixture that returns a canned response (avoids actual API calls)
  - `mock_event_bus`: No-op event bus for testing single agents

### 10.2 Test Plan

**test_tools.py (5 tests):**
1. `test_get_all_products` — Returns all products from test DB
2. `test_search_products` — Keyword search returns correct subset
3. `test_get_order_by_id` — Found and not-found cases
4. `test_get_fraud_signals` — Signal calculation correctness
5. `test_append_order` — Creates order, updates inventory

**test_agents.py (8 tests):**
1. `test_support_agent_routing` — Support keywords route correctly
2. `test_inventory_agent_availability` — Returns stock info
3. `test_inventory_agent_no_match` — Gracefully handles missing products
4. `test_fraud_agent_specific_order` — CrewAI pipeline runs
5. `test_fraud_agent_sweep` — Full order sweep returns results
6. `test_order_agent_create` — Order lifecycle: create → confirm
7. `test_order_agent_cancel` — Order cancellation flow
8. `test_pricing_agent_analysis` — Generates sale suggestions

**test_workflows.py (3 tests):**
1. `test_order_placed_event_chain` — Place order → verify fraud + inventory triggered
2. `test_supervisor_routing` — Each query type routes to correct agent
3. `test_cross_agent_query` — Support agent can query inventory via event bus

---

## 11. Config System

Central configuration in `commerceos/config.py`:

```python
class Settings(BaseSettings):
    # LLM
    groq_api_key: str
    llm_model: str = "qwen/qwen3-32b"
    fraud_llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.3
    
    # Database
    database_url: str = "sqlite:///data/commerceos.db"
    
    # Store
    store_name: str = "Urban Thread Co."
    tax_rate: float = 0.08
    
    # Agent settings
    low_stock_threshold_ratio: float = 1.0  # >= reorder_threshold = low
    max_chat_history: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

All modules import `from commerceos.config import settings` instead of reading `os.getenv` directly.

---

## 12. Migration Path: Current → Target

### Phase A: Reorganize & Refactor (Day 1-2)
- Create new `commerceos/` package structure
- Move existing files into new structure (preserving imports)
- No behavior changes — just relocating code

### Phase B: Database Layer (Day 3-4)
- Build SQLAlchemy models
- Create database connection module
- Write seed script to import CSVs
- Update MCP tools to use DB instead of CSV

### Phase C: Event System + Auto-Triggers (Day 5-6)
- Build EventBus
- Build ActivityTracker
- Wire up order.created → fraud + inventory chain
- Wire up stock.low → admin alert

### Phase D: New Agents + Dashboard (Day 7-9)
- Implement Order Agent (order lifecycle)
- Implement Pricing Agent (sale analysis)
- Build Admin Dashboard page
- Build Order History page

### Phase E: UI Polish + Tests (Day 10-12)
- Product images + category filter
- Cart fixes (buy all, order summary)
- Write 15+ tests
- Final polish on loading/empty/error states

### Phase F: Infrastructure + Docs (Day 13-14)
- Dockerize the application
- Set up Alembic migrations
- Write professional README with architecture diagram
- Update CLAUDE.md
- Git init with structured commits

---

## 13. Design Decisions & Trade-offs

| Decision | Why | Trade-off |
|---|---|---|
| SQLite (not PostgreSQL) | Zero deps, portable. One `docker compose up` and it works | Not horizontally scalable. Fine for portfolio/MVP |
| In-process event bus (not Redis/RabbitMQ) | No external broker dependency. Simpler code | Events lost if process crashes. Fine for single-container deployment |
| Agent registry (not hardcoded routing) | Adding agents doesn't change supervisor code | Slightly more indirection. Worth it for extensibility |
| LangChain for agents (not raw LLM calls) | Consistent with existing codebase. Shows framework knowledge | Heavier dependency. Frameworks are the norm in agentic AI |
| CrewAI for fraud (not single LLM call) | Demonstrates multi-role architecture. Already exists and works | Two LLM calls instead of one. The architectural demonstration is valuable for portfolio |
| SQLAlchemy ORM (not raw SQL) | Shows professional database patterns. Migrations are clean | ORM overhead is negligible for SQLite |

---

## 14. File Inventory (Final)

**Total files created:** ~30
**Total files modified:** ~10
**Existing files removed:** ~5 (merged into new structure)

### New Files (25)
```
commerceos/__init__.py
commerceos/config.py
commerceos/agents/__init__.py
commerceos/agents/base.py
commerceos/agents/registry.py
commerceos/agents/order_agent.py
commerceos/agents/pricing_agent.py
commerceos/orchestration/__init__.py
commerceos/orchestration/supervisor.py       # replaces root supervisor.py
commerceos/orchestration/event_bus.py
commerceos/orchestration/workflows.py
commerceos/mcp/__init__.py
commerceos/mcp/registry.py
commerceos/database/__init__.py
commerceos/database/models.py
commerceos/database/connection.py
commerceos/database/seed.py
commerceos/observability/__init__.py
commerceos/observability/logger.py
commerceos/observability/activity_tracker.py
pages/order_history.py
pages/admin_dashboard.py
ui/components.py
ui/assets/images/gen_placeholders.py
infrastructure/Dockerfile
infrastructure/docker-compose.yml
infrastructure/entrypoint.sh
infrastructure/alembic/alembic.ini
infrastructure/alembic/env.py
tests/conftest.py
tests/test_tools.py
tests/test_agents.py
tests/test_workflows.py
scripts/setup.sh
scripts/seed.py
docs/architecture.md
pyproject.toml
.github/workflows/ci.yml
```

### Modified Files (8)
```
app.py                              # Updated imports, category filter, sale badges
pages/cart.py                       # Buy all items, order summary
pages/ai_assistant.py               # Updated imports, better UX
mcp_server/tools.py → commerceos/mcp/tools.py   # DB-backed, refactored
agents/fraud_agent.py → commerceos/agents/
agents/support_agent.py → commerceos/agents/
agents/inventory_agent.py → commerceos/agents/
rag/vectorstore_setup.py → rag/vectorstore.py
```

### Removed (merged into new structure)
```
supervisor.py                       # → commerceos/orchestration/supervisor.py
utils/styling.py                    # → ui/styling.py
mcp_server/tools.py                 # → commerceos/mcp/tools.py (refactored)
agents/support_agent.py             # → commerceos/agents/
agents/inventory_agent.py           # → commerceos/agents/
agents/fraud_agent.py               # → commerceos/agents/
rag/vectorstore_setup.py            # → rag/vectorstore.py
```
