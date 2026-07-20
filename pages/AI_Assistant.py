"""
pages/AI_Assistant.py — AI chat panel with 5-agent routing.
"""
import streamlit as st
import time
from ui.styling import inject_custom_css


@st.cache_resource(show_spinner=False)
def _get_supervisor():
    from commerceos.orchestration.supervisor import handle_query as _hq
    return _hq


@st.cache_resource(show_spinner=False)
def _prewarm_engine():
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

if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())[:8]
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "_engine_warmed" not in st.session_state:
    st.session_state._engine_warmed = False

if not st.session_state._engine_warmed:
    with st.spinner("🔄 Initializing AI engine..."):
        _prewarm_engine()
        st.session_state._engine_warmed = True
    st.rerun()

# ── Sidebar ──
show_ops = st.sidebar.checkbox("Show Ops Alerts (Admin Mode)", value=False)
st.sidebar.caption(f"Session ID: `{st.session_state.thread_id}`")
if st.sidebar.button("Clear conversation"):
    st.session_state.chat_log = []
    st.rerun()

with st.expander("ℹ️ How this works (architecture)"):
    st.markdown("""
    - **Supervisor (LangGraph + Memory)** routes to 5 specialist agents
    - **Support Agent** uses RAG over store policy + order lookups
    - **Inventory Agent** queries live product catalog via MCP tool layer
    - **Fraud Agent** runs CrewAI 2-role crew (Signal Analyst → Risk Adjudicator)
    - **Order Agent** manages order lifecycle, tracking, cancellations
    - **Pricing Agent** handles sales, discounts, and dynamic pricing
    - All agents share the **MCP tool layer** + **EventBus** for collaboration
    """)

# ── Example buttons ──
st.markdown("**Try an example:**")
col1, col2, col3, col4, col5 = st.columns(5)
examples = [
    "Where is my order O2001?",
    "Do we have the white t-shirt in stock?",
    "Check order O2004 for fraud",
    "Any items on sale right now?",
    "Cancel order O2005",
]

_clicked_example = None
for col, example in zip([col1, col2, col3, col4, col5], examples):
    if col.button(example, key=f"ex_{example[:8]}", use_container_width=True):
        _clicked_example = example

# ── Chat form ──
with st.form("chat_form", clear_on_submit=True):
    user_query = st.text_input(
        "Type your message:",
        placeholder="e.g. Can I return a damaged item from order O2010?",
        key="main_input",
    )
    submitted = st.form_submit_button("Submit", type="primary")

query_to_run = _clicked_example or (user_query if submitted else "")

if query_to_run and query_to_run.strip():
    query_text = query_to_run.strip()

    status_placeholder = st.empty()
    step_messages = {
        "support": ["🔎 Searching policies...", "📄 Consulting support agent...", "✍️ Crafting response..."],
        "inventory": ["📦 Checking stock levels...", "🛒 Consulting inventory agent...", "✍️ Crafting response..."],
        "fraud": ["🔍 Analyzing fraud signals...", "🕵️ Running analyst review...", "⚖️ Making risk decision..."],
        "order": ["📋 Looking up order...", "🔄 Checking status...", "✍️ Crafting response..."],
        "pricing": ["🏷️ Checking prices...", "📊 Analyzing sales...", "✍️ Crafting response..."],
        "default": ["🤔 Analyzing your request...", "🔄 Routing to specialist...", "✍️ Generating response..."],
    }

    for msg in step_messages["default"]:
        status_placeholder.info(msg)
        time.sleep(0.15)

    with st.spinner(""):
        result = handle_query(query_text, thread_id=st.session_state.thread_id)

    status_placeholder.empty()

    st.session_state.chat_log.append({
        "query": query_text,
        "agent": result["agent_name"],
        "answer": result["answer"],
        "ops_alert": result.get("ops_alert", ""),
        "context": result["context_used"],
    })
    st.rerun()

# ── Display conversation ──
if not st.session_state.chat_log:
    st.info("👋 Ask me anything about orders, inventory, pricing, or fraud detection!")

for entry in reversed(st.session_state.chat_log):
    agent_name = entry["agent"]
    an_lower = agent_name.lower()

    if "fraud" in an_lower:
        badge, badge_color = "🛡️ Fraud Detection", "#ef4444"
    elif "inventory" in an_lower:
        badge, badge_color = "📦 Inventory Agent", "#f59e0b"
    elif "support" in an_lower:
        badge, badge_color = "🎧 Support Agent", "#3b82f6"
    elif "order" in an_lower:
        badge, badge_color = "📋 Order Agent", "#8b5cf6"
    elif "pricing" in an_lower:
        badge, badge_color = "🏷️ Pricing Agent", "#10b981"
    else:
        badge, badge_color = "🤖 AI Assistant", "#636e72"

    st.markdown(
        f"<div class='chat-message user'>"
        f"<div class='chat-label'>🧑 You</div>"
        f"{entry['query']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='chat-message agent'>"
        f"<div class='chat-label' style='color:{badge_color}'>{badge}</div>"
        f"{entry['answer']}</div>",
        unsafe_allow_html=True,
    )

    if show_ops and entry.get("ops_alert"):
        with st.expander("⚠️ Internal Ops Alert (Admin Only)"):
            st.warning(entry["ops_alert"])
