# CommerceOS AI

## Overview
An **autonomous multi-agent e-commerce operations system** with a live Streamlit storefront ("Urban Thread Co."). A LangGraph Supervisor routes user queries to specialist agents — each using a distinct AI framework chosen for its specific job.

## Quick Start
```bash
# 1. Activate venv
source venv/Scripts/activate  # Git Bash on Windows
# or: venv\Scripts\activate   # CMD

# 2. Build vectorstore (one-time)
python rag/vectorstore_setup.py

# 3. Test individual agents
python agents/support_agent.py
python agents/inventory_agent.py
python agents/fraud_agent.py

# 4. Test supervisor routing
python supervisor.py

# 5. Run storefront
streamlit run app.py
```

## Architecture

```
Streamlit Storefront (Browse | Cart | AI Assistant)
        │
        ▼
LangGraph SUPERVISOR (MemorySaver checkpointer)
  reads query + session history → routes to one agent via keywords or LLM fallback
        │
   ┌────┼────┐
   ▼    ▼    ▼
Support  Inventory  Fraud
LangChain MCP calls  CrewAI
 + RAG    + LLM      2 roles
   │    reasoning    (Signal Analyst → Risk Adjudicator)
   └────┼────┘
        ▼
MCP TOOL LAYER (shared data access via mcp_server/tools.py)
  products.csv | orders.csv | refund_policy.txt
```

## Project Structure

```
commerceos-ai/
├── app.py                      # Streamlit home page — product grid, cart session
├── supervisor.py               # LangGraph supervisor with keyword-first routing + MemorySaver
├── agents/
│   ├── support_agent.py        # RAG (ChromaDB) + order lookups via MCP tools
│   ├── inventory_agent.py      # MCP tool searches → customer answer + background ops alert
│   └── fraud_agent.py          # CrewAI 2-role crew (sequential: Analyst → Adjudicator)
├── mcp_server/
│   └── tools.py                # Shared MCP-pattern tool registry (CSV-backed)
├── rag/
│   └── vectorstore_setup.py    # Builds/loads ChromaDB from refund_policy.txt
├── pages/
│   ├── 1_Cart_Checkout.py      # Cart view, quantity adjust, simulated checkout
│   └── 2_AI_Assistant.py       # AI chat panel with admin mode toggle for ops alerts
├── data/
│   ├── products.csv            # Product catalog + stock levels + reorder thresholds
│   ├── orders.csv              # Order history (includes planted fraud patterns)
│   ├── refund_policy.txt       # Store policy (15 sections) — source for RAG
│   └── chroma_store/           # Auto-generated vector DB (gitignored)
├── requirements.txt
├── .env                        # GROQ_API_KEY (gitignored)
└── CLAUDE.md                   # This file
```

## Key Technical Details

### API Key
- **Groq API** is the LLM provider (set in `.env`: `GROQ_API_KEY=...`)
- Free tier available at https://console.groq.com
- Models used: `qwen/qwen3-32b` (Supervisor, Support, Inventory) and `llama-3.3-70b-versatile` (CrewAI fraud agent via LiteLLM)
- CrewAI uses LiteLLM internally — model format is `groq/<model-name>` but passed as `LLM(model="llama-3.3-70b-versatile")`

### LangGraph Supervisor (`supervisor.py`)
- **State**: `GraphState` TypedDict with `user_query`, `route`, `agent_name`, `answer`, `ops_alert`, `context_used`, `history`
- **Routing**: keyword pre-check first (fraud/inventory keywords), LLM fallback for support
- **Memory**: `MemorySaver` checkpointer — sessions identified by `thread_id` string
- Conditional edges: supervisor → one of {support, inventory, fraud} → END

### Agent Details

**Support Agent** (`agents/support_agent.py`):
- Uses RAG (ChromaDB, HuggingFace `all-MiniLM-L6-v2` embeddings) to retrieve policy context
- Extracts order IDs (regex: O####) for order-specific lookups via MCP tools
- Grounds answers in real policy text — says so if policy doesn't cover the question

**Inventory Agent** (`agents/inventory_agent.py`):
- Dual-output architecture: customer-facing answer + ops alert (internal)
- Customer answer is clean, conversational — never exposes reorder thresholds or IDs
- Ops alert flagged in `ops_alert` field (shown in AI Assistant when admin toggle is on)

**Fraud Agent** (`agents/fraud_agent.py`):
- CrewAI sequential crew: **Signal Analyst** (neutral interpretation) → **Risk Adjudicator** (final: APPROVE / HOLD FOR REVIEW / REJECT)
- Includes monkey-patch for `crewai.llms.cache.mark_cache_breakpoint` (Groq rejects the `cache_breakpoint` field)
- `build_fraud_crew()` creates a fresh crew per request
- Handles both specific order checks and general "any suspicious orders?" sweeps

### MCP Tool Layer (`mcp_server/tools.py`)
Centralized data access — all agents call `call_tool(tool_name, **kwargs)` instead of reading CSVs directly.
Tools: `get_all_products`, `search_products`, `get_low_stock_products`, `get_product_by_id`, `get_order_by_id`, `get_fraud_signals`, `get_all_flagged_orders`

### RAG Setup (`rag/vectorstore_setup.py`)
- One-time build: chunks `refund_policy.txt` (chunk_size=500, overlap=50), embeds with `all-MiniLM-L6-v2`, persists to `data/chroma_store/`
- `load_vectorstore()` uses module-level singleton cache
- Re-run when `refund_policy.txt` changes

### Data Files
- **products.csv**: product_id, product_name, category, price, stock_quantity, reorder_threshold
- **orders.csv**: order_id, customer_name, customer_email, customer_account_age_days, product_id, order_amount, order_timestamp, shipping_country, billing_country
- Fraud signals check: velocity (15-min window), country mismatch, new account + high value, disposable email markers

### Streamlit Storefront
- `app.py` — product grid with search, add-to-cart buttons, session state cart
- `pages/1_Cart_Checkout.py` — cart display, qty adjustment, simulated checkout (no real payment)
- `pages/2_AI_Assistant.py` — query input, example buttons, conversation log, "Show Ops Alerts" admin toggle
- Session ID (`thread_id`) generated per browser tab for LangGraph memory

## Important Gotchas
- CrewAI's `cache_breakpoint` field is monkey-patched to a no-op — removing this causes Groq API errors
- Vectorstore must be built (`python rag/vectorstore_setup.py`) before running support agent
- `.env` file is in `.gitignore` — never commit real API keys
- `data/chroma_store/` is gitignored — must be rebuilt on fresh clones
- The `.env` example has a real key checked in (`.env` not `.env.example`) — should rotate that key

## Roadmap (Phase 2 — Not Yet Built)
- Pricing Optimization Agent (dynamic pricing)
- Reporting Agent (cross-agent daily summary)
- ML-based fraud scoring on top of rule-based signals
- Real MCP server transport (currently local pattern only)
- Cross-agent shared memory beyond single-session scope
