# CommerceOS AI

**Autonomous Multi-Agent E-commerce Operations System**

CommerceOS AI is a multi-agent system powering both a real storefront and an
autonomous operations layer. A LangGraph Supervisor (with session memory)
reads incoming messages and routes them to the right specialist agent —
Customer Support, Inventory, or Fraud Detection — instead of running a fixed
pipeline. Each agent uses the framework best suited to its actual job, not
frameworks added for their own sake.

## Architecture

```
                     STREAMLIT STOREFRONT
        (Browse Products | Cart & Checkout | AI Assistant)
                              |
                              v
            LANGGRAPH SUPERVISOR (MemorySaver checkpointer)
         reads query + session history -> routes to one agent
                              |
       +----------------------+----------------------+
       |                      |                       |
       v                      v                       v
 SUPPORT AGENT          INVENTORY AGENT           FRAUD AGENT
 LangChain + RAG        MCP tool calls            CrewAI (2 roles):
 (ChromaDB, grounded     (live stock lookup        Signal Analyst ->
 in real policy text)    + reasoning)               Risk Adjudicator
       |                      |                       |
       +----------------------+----------------------+
                              |
                              v
                  MCP TOOL LAYER (shared data access)
            products.csv | orders.csv | refund_policy.txt
```

## Why each framework is there (no redundant stacking)

- **LangGraph + MemorySaver**: orchestration spine. Routes each query via a
  conditional edge, and remembers session history (via a checkpointer +
  thread_id) so later queries in the same session have context from earlier
  ones.
- **LangChain + RAG/ChromaDB**: grounds Support Agent answers in the actual
  refund policy text instead of letting the LLM guess.
- **CrewAI**: used specifically where two-step structured reasoning adds
  real value — fraud decisions benefit from a Signal Analyst (objectively
  reads the data) followed by a Risk Adjudicator (makes the final call based
  on that interpretation). This is genuine multi-agent collaboration, not a
  routing decision.
- **MCP tool layer**: all data access (products, orders, fraud signals) goes
  through a single shared tool registry (`mcp_server/tools.py`) instead of
  each agent independently reading CSVs. This implements MCP's tool-calling
  *pattern* locally — built so it could later be swapped for a real networked
  MCP server transport without changing any agent logic.
- **AutoGen was evaluated and intentionally not used** — its strength
  (open-ended multi-agent dialogue) overlaps with what CrewAI already does
  here, and adding both would mean two frameworks doing the same job rather
  than each having a distinct purpose.

## Project Structure

```
commerceos-ai/
├── data/
│   ├── products.csv          # product catalog with stock levels
│   ├── orders.csv            # order history (includes planted fraud patterns)
│   ├── refund_policy.txt     # store policy used for RAG
│   └── chroma_store/         # generated automatically — the vector database
├── agents/
│   ├── support_agent.py      # LangChain + RAG
│   ├── inventory_agent.py    # MCP tool calls + LLM reasoning
│   └── fraud_agent.py        # CrewAI 2-role crew
├── mcp_server/
│   └── tools.py               # shared MCP-pattern tool registry
├── rag/
│   └── vectorstore_setup.py
├── pages/
│   ├── 1_Cart_Checkout.py     # storefront cart/checkout
│   └── 2_AI_Assistant.py      # CommerceOS AI control panel
├── supervisor.py               # LangGraph routing brain (with memory)
├── app.py                      # Streamlit storefront home page
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Create a virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
Note: this installs CrewAI in addition to the LangChain/LangGraph stack —
expect this step to take a few minutes.

### 3. Get a Groq API key and set up your .env file
Go to https://console.groq.com, create a free account, and generate an API key.

Create a `.env` file in the project root (copy `.env.example` and rename it),
then add your real key:
```
GROQ_API_KEY=your_actual_key_here
```

### 4. Build the vectorstore (run ONCE)
```bash
python rag/vectorstore_setup.py
```

### 5. Test each agent individually (recommended before running the full app)
```bash
python agents/support_agent.py
python agents/inventory_agent.py
python agents/fraud_agent.py
```

### 6. Test the full Supervisor routing (including memory)
```bash
python supervisor.py
```
This runs two queries in the same session — the second one should show
the system using context from the first.

### 7. Run the storefront
```bash
streamlit run app.py
```
This opens the storefront home page. Use the sidebar to navigate to
**Cart & Checkout** or the **AI Assistant** panel.

## Example Queries to Try (in the AI Assistant page)

- "Where is my order O2001?" → routes to **Support Agent**
- "Can I return earrings I bought?" → routes to **Support Agent**
- "Do we have the white t-shirt in stock?" → routes to **Inventory Agent**
- "What products need restocking?" → routes to **Inventory Agent**
- "Check order O2004 for fraud" → routes to **Fraud Agent** (watch the
  transparency log — you'll see the Signal Analyst's interpretation feed
  into the Risk Adjudicator's final decision)

## Roadmap (Phase 2 — Not Yet Built)

- Pricing Optimization Agent (dynamic pricing based on demand)
- Reporting Agent (daily cross-agent operational summary)
- ML-based fraud scoring layered on top of current rule-based signals
- Real MCP server transport (currently the tool-calling pattern only,
  implemented locally rather than over a networked protocol)
- Cross-agent shared memory beyond a single session (e.g. persisting
  flagged-customer context across separate visits, not just one session)

## Tech Stack

LangChain, LangGraph (+ MemorySaver), ChromaDB (RAG), CrewAI, Groq API,
Streamlit, pandas
