"""
supervisor.py
LangGraph Supervisor with memory + keyword-first routing.
"""

import re
from typing import TypedDict, Literal, Annotated
from operator import add
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq

load_dotenv()


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
    query_lower = query.lower()
    history = state.get("history", [])

    # Keyword pre-check before LLM — catches typos and short queries
    # NOTE: "check/verify order" is NOT here intentionally — those go to Support
    fraud_keywords = ["fraud", "suspicious", "scam", "fake",
                      "fraudulent"]
    inventory_keywords = ["stock", "inventory", "available", "restock",
                          "quantity", "in stock", "out of stock", "how many",
                          "do we have", "do you have", "is there"]

    if any(kw in query_lower for kw in fraud_keywords):
        state["route"] = "fraud"
        return state

    if any(kw in query_lower for kw in inventory_keywords):
        state["route"] = "inventory"
        return state

    # LLM fallback for everything else
    history_text = ""
    if history:
        recent = history[-3:]
        history_text = "Recent session history:\n" + "\n".join(
            [f"- [{h['agent']}] Q: {h['query']} -> A: {h['answer'][:100]}..." for h in recent]
        )

    classification_prompt = (
        "You are a routing classifier for an e-commerce system. "
        "Classify the message into ONE category:\n\n"
        "- 'support': orders, refunds, returns, complaints, shipping, payment, how to buy\n"
        "- 'inventory': stock levels, product availability\n"
        "- 'fraud': checking if an order is suspicious or fraudulent\n\n"
        f"{history_text}\n\n"
        "Reply with ONLY one word: support, inventory, or fraud.\n\n"
        f"Message: \"{query}\"\n\nCategory:"
    )

    llm = ChatGroq(model="qwen/qwen3-32b", temperature=0)
    response = llm.invoke(classification_prompt)
    decision = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip().lower()

    if decision not in ["support", "inventory", "fraud"]:
        decision = "support"

    state["route"] = decision
    return state


def route_decision(state: GraphState) -> Literal["support", "inventory", "fraud"]:
    return state["route"]


def _record_history(state: GraphState, result: dict) -> GraphState:
    state["agent_name"] = result["agent"]
    state["answer"] = result["answer"]
    state["ops_alert"] = result.get("ops_alert", "")
    state["context_used"] = result["context_used"]
    state["history"] = [{
        "query": state["user_query"],
        "agent": result["agent"],
        "answer": result["answer"],
    }]
    return state


def support_node(state: GraphState) -> GraphState:
    from agents.support_agent import run_support_agent
    try:
        result = run_support_agent(state["user_query"])
    except Exception as e:
        return _error_state(state, f"Support agent encountered an error: {e}")
    return _record_history(state, result)


def inventory_node(state: GraphState) -> GraphState:
    from agents.inventory_agent import run_inventory_agent
    try:
        result = run_inventory_agent(state["user_query"])
    except Exception as e:
        return _error_state(state, f"Inventory agent encountered an error: {e}")
    return _record_history(state, result)


def fraud_node(state: GraphState) -> GraphState:
    from agents.fraud_agent import run_fraud_agent
    try:
        result = run_fraud_agent(state["user_query"])
    except Exception as e:
        return _error_state(state, f"Fraud detection agent encountered an error: {e}")
    return _record_history(state, result)


def _error_state(state: GraphState, message: str) -> GraphState:
    state["agent_name"] = "System"
    state["answer"] = f"I ran into a problem: {message}\n\nPlease try rephrasing your question or contact support if the issue persists."
    state["ops_alert"] = ""
    state["context_used"] = ""
    state["history"] = [{"query": state["user_query"], "agent": "System", "answer": message}]
    return state


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("support", support_node)
    graph.add_node("inventory", inventory_node)
    graph.add_node("fraud", fraud_node)
    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor", route_decision,
        {"support": "support", "inventory": "inventory", "fraud": "fraud"},
    )
    graph.add_edge("support", END)
    graph.add_edge("inventory", END)
    graph.add_edge("fraud", END)
    return graph.compile(checkpointer=MemorySaver())


commerceos_graph = build_graph()


def handle_query(user_query: str, thread_id: str = "default-session") -> dict:
    if not user_query or not user_query.strip():
        return {
            "user_query": "",
            "route": "",
            "agent_name": "System",
            "answer": "Please type a question or select an example above. I can help with orders, inventory, and fraud detection.",
            "ops_alert": "",
            "context_used": "",
            "history": [],
        }
    initial_state = {
        "user_query": user_query,
        "route": "",
        "agent_name": "",
        "answer": "",
        "ops_alert": "",
        "context_used": "",
        "history": [],
    }
    config = {"configurable": {"thread_id": thread_id}}
    return commerceos_graph.invoke(initial_state, config)


if __name__ == "__main__":
    r1 = handle_query("Do you have white t-shirt in stock?")
    print(f"Customer sees: {r1['answer']}")
    print(f"Ops alert: {r1['ops_alert']}")