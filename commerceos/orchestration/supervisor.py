"""LangGraph Supervisor with AgentRegistry routing + MemorySaver."""
import re
from operator import add
from typing import Annotated, Literal, TypedDict

from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from commerceos.agents import AgentRegistry
from commerceos.config import settings
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

    route_match = AgentRegistry.route(query)
    if route_match:
        state["route"] = route_match
        track("Supervisor", "route", f"Keyword -> {route_match}: {query[:50]}")
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
    except Exception as e:  # noqa: BLE001
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
    """Route a user query through the LangGraph supervisor.

    The supervisor first checks keyword routing via ``AgentRegistry``,
    then falls back to an LLM for ambiguous queries. The selected agent
    runs and its result is returned.

    Args:
        user_query: The raw text from the user.
        thread_id: Session identifier for MemorySaver continuity.

    Returns:
        A dict with keys: ``user_query``, ``route``, ``agent_name``,
        ``answer``, ``ops_alert``, ``context_used``, ``history``.
    """
    if not user_query or not user_query.strip():
        return {"user_query": "", "route": "", "agent_name": "System",
                "answer": "Please type a question.", "ops_alert": "",
                "context_used": "", "history": []}
    initial = {"user_query": user_query, "route": "", "agent_name": "",
               "answer": "", "ops_alert": "", "context_used": "", "history": []}
    result = commerceos_graph.invoke(initial, {"configurable": {"thread_id": thread_id}})
    return result
