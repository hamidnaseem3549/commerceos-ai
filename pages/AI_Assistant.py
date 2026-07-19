"""
pages/2_AI_Assistant.py

PURPOSE:
CommerceOS AI Assistant panel with example buttons that auto-submit,
form-based submission (Enter key works), step-by-step loading stages,
professional chat bubbles, and admin-level ops alert visibility.
"""

import streamlit as st
import time

from utils.styling import inject_custom_css


@st.cache_resource(show_spinner=False)
def _get_supervisor():
    from supervisor import handle_query as _hq
    return _hq


@st.cache_resource(show_spinner=False)
def _prewarm_engine():
    """Pre-warm the vectorstore and LLM connection so the first user
    query is fast instead of paying a cold-start penalty."""
    from rag.vectorstore_setup import load_vectorstore
    load_vectorstore()
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="qwen/qwen3-32b", temperature=0)
    llm.invoke("Say 'ready' in one word.")
    return True


handle_query = _get_supervisor()

st.set_page_config(page_title="CommerceOS AI Assistant", page_icon="🤖", layout="wide")
inject_custom_css()
st.title("🤖 CommerceOS AI — Assistant Panel")
st.caption("A Supervisor Agent routes your message to the right specialist agent in real time.")

# ── Session state ──
if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())[:8]

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "_engine_warmed" not in st.session_state:
    st.session_state._engine_warmed = False

# ── Pre-warm engine on first load with visible progress ──
if not st.session_state._engine_warmed:
    with st.spinner("🔄 Initializing AI engine..."):
        _prewarm_engine()
        st.session_state._engine_warmed = True
    st.rerun()

# ── Sidebar controls ──
show_ops = st.sidebar.checkbox("Show Ops Alerts (Admin Mode)", value=False)
st.sidebar.caption(f"Session ID: `{st.session_state.thread_id}`")
if st.sidebar.button("Clear conversation"):
    st.session_state.chat_log = []
    st.rerun()

# ── Architecture expander ──
with st.expander("ℹ️ How this works (architecture)"):
    st.markdown("""
    - **Supervisor (LangGraph + Memory)** routes your message to the right specialist agent
    - **Customer Support Agent** uses RAG over store policy + order lookups
    - **Inventory Agent** queries live product catalog via MCP tool layer
    - **Fraud Detection Agent** runs CrewAI 2-role crew (Signal Analyst → Risk Adjudicator)
    - All agents share the same **MCP tool layer** for data access
    """)

# ── Example buttons (auto-submit on click) ──
st.markdown("**Try an example:**")
col1, col2, col3 = st.columns(3)
examples = [
    "Where is my order O2001?",
    "Do we have the white t-shirt in stock?",
    "Check order O2004 for fraud",
]

# Capture which example was clicked (if any) BEFORE the form renders.
# This way clicking an example button immediately triggers a query.
_clicked_example = None
for col, example in zip([col1, col2, col3], examples):
    if col.button(example, key=f"ex_{example[:8]}"):
        _clicked_example = example

# ── Main chat form (Enter key submits!) ──
with st.form("chat_form", clear_on_submit=True):
    user_query = st.text_input(
        "Type your message:",
        placeholder="e.g. Can I return a damaged item from order O2010?",
        key="main_input",
    )
    submitted = st.form_submit_button("Submit", type="primary")

# Resolve what to process: clicked example takes priority, else form input
query_to_run = _clicked_example or (user_query if submitted else "")

if query_to_run and query_to_run.strip():
    query_text = query_to_run.strip()

    # Step-by-step progress simulation
    status_placeholder = st.empty()
    step_messages = {
        "support": ["🔎 Searching policies...", "📄 Consulting support agent...", "✍️ Crafting response..."],
        "inventory": ["📦 Checking stock levels...", "🛒 Consulting inventory agent...", "✍️ Crafting response..."],
        "fraud": ["🔍 Analyzing fraud signals...", "🕵️ Running analyst review...", "⚖️ Making risk decision..."],
        "default": ["🤔 Analyzing your request...", "🔄 Routing to specialist...", "✍️ Generating response..."],
    }

    # Show default steps while routing is determined
    for msg in step_messages["default"]:
        status_placeholder.info(msg)
        time.sleep(0.15)

    # Run the actual query through the LangGraph supervisor
    with st.spinner(""):
        result = handle_query(query_text, thread_id=st.session_state.thread_id)

    status_placeholder.empty()

    # Determine which progress messages would have been shown
    route_key = result.get("agent_name", "").lower()

    st.session_state.chat_log.append({
        "query": query_text,
        "agent": result["agent_name"],
        "answer": result["answer"],
        "ops_alert": result.get("ops_alert", ""),
        "context": result["context_used"],
    })
    st.rerun()

# ── Display conversation (most recent first) ──
if not st.session_state.chat_log:
    st.info("👋 Ask me anything about orders, inventory, or fraud detection!")

for entry in reversed(st.session_state.chat_log):
    agent_name = entry["agent"]

    # Determine agent badge styling
    if "fraud" in agent_name.lower():
        badge = "🛡️ Fraud Detection"
        badge_color = "#ef4444"
    elif "inventory" in agent_name.lower():
        badge = "📦 Inventory Agent"
        badge_color = "#f59e0b"
    elif "support" in agent_name.lower():
        badge = "🎧 Support Agent"
        badge_color = "#3b82f6"
    else:
        badge = "🤖 AI Assistant"
        badge_color = "#636e72"

    # User message bubble
    st.markdown(
        f"<div class='chat-message user'>"
        f"<div class='chat-label'>🧑 You</div>"
        f"{entry['query']}</div>",
        unsafe_allow_html=True,
    )

    # Agent response bubble
    st.markdown(
        f"<div class='chat-message agent'>"
        f"<div class='chat-label' style='color:{badge_color}'>{badge}</div>"
        f"{entry['answer']}</div>",
        unsafe_allow_html=True,
    )

    # Ops alert — admin-only via sidebar toggle
    if show_ops and entry.get("ops_alert"):
        with st.expander("⚠️ Internal Ops Alert (Admin Only)"):
            st.warning(entry["ops_alert"])
