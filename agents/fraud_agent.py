"""
agents/fraud_agent.py

PURPOSE:
Fraud detection rebuilt using CrewAI's role-based collaboration pattern.

WHY CREWAI HERE SPECIFICALLY:
Fraud decisions benefit from a genuine two-step judgment process:
  1. First, objectively read what the data signals say (no opinion yet)
  2. Then, separately, weigh those signals and make a risk call

Doing this as ONE LLM call (as the original version did) collapses both
steps into a single pass, which is faster but shallower. CrewAI lets us
model this as two distinct roles with two distinct responsibilities,
where the second role's task explicitly receives the first role's output
as input. This is real multi-agent collaboration, not routing.

THE TWO ROLES:
  - Signal Analyst: reads the raw fraud signal data (from MCP tools) and
    writes an objective, neutral interpretation of what was found.
  - Risk Adjudicator: reads the Signal Analyst's interpretation and makes
    the final call -- approve, hold for review, or reject -- with reasoning.

DATA ACCESS:
All raw data comes through mcp_server/tools.py, NOT direct pandas calls.
This keeps the agent decoupled from how/where the data is actually stored.
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

# Monkey-patch CrewAI's cache_breakpoint to a no-op — it inserts
# "cache_breakpoint": True into every message dict, which LiteLLM then
# serializes and sends to the LLM provider. Groq rejects this field.
# Since all our models are non-Anthropic (Groq), caching is irrelevant.
import crewai.llms.cache as _crew_cache
_original_mark = _crew_cache.mark_cache_breakpoint
_crew_cache.mark_cache_breakpoint = lambda msg: msg

from mcp_server.tools import call_tool

load_dotenv()

# CrewAI works with LiteLLM-style model strings. For Groq, the format is
# "groq/<model_name>". We define this once and reuse it for both roles.
groq_llm = LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2)


def extract_order_id(text: str):
    """Simple rule-based extractor for our O#### order ID format."""
    words = text.replace("#", " ").replace(",", " ").split()
    for word in words:
        if word.upper().startswith("O") and word[1:].isdigit():
            return word.upper()
    return None


def build_fraud_crew(signal_data_text: str, order_id: str):
    """
    Builds the 2-agent CrewAI crew for a single fraud analysis run.
    A fresh crew is built per request (not reused) since each one
    operates on different order data.
    """

    signal_analyst = Agent(
        role="Fraud Signal Analyst",
        goal="Objectively interpret raw fraud detection signals without making a final judgment call.",
        backstory=(
            "You are a data analyst at an e-commerce trust & safety team. "
            "Your job is ONLY to read computed fraud signals and describe, "
            "in clear factual language, what was found. You do not decide "
            "whether to approve or reject orders -- that is not your role. "
            "You never invent numbers beyond what you're given."
        ),
        llm=groq_llm,
        verbose=False,
    )

    risk_adjudicator = Agent(
        role="Risk Adjudicator",
        goal="Make a final, justified risk decision based on the Signal Analyst's findings.",
        backstory=(
            "You are a senior fraud risk manager. You receive the Signal "
            "Analyst's interpretation and must make ONE final call: APPROVE "
            "(looks safe), HOLD FOR MANUAL REVIEW (suspicious, needs a human), "
            "or REJECT (clearly fraudulent). You always state your reasoning "
            "and reference the specific signals that drove your decision."
        ),
        llm=groq_llm,
        verbose=False,
    )

    analyze_task = Task(
        description=(
            f"Here is the raw fraud signal data for order {order_id}:\n\n"
            f"{signal_data_text}\n\n"
            "Write a short, objective interpretation of what these signals "
            "indicate. Do not make a final approve/reject decision -- just "
            "describe what was found and why each triggered signal is "
            "potentially meaningful."
        ),
        expected_output="A factual, neutral paragraph interpreting the fraud signals.",
        agent=signal_analyst,
    )

    adjudicate_task = Task(
        description=(
            "Based on the Signal Analyst's interpretation above, make your "
            "final risk decision for this order. Respond in this exact format:\n\n"
            "DECISION: [APPROVE / HOLD FOR MANUAL REVIEW / REJECT]\n"
            "REASONING: [your explanation, referencing specific signals]"
        ),
        expected_output="A clear decision with reasoning, in the specified format.",
        agent=risk_adjudicator,
        context=[analyze_task],  # this is what passes Analyst's output into this task
    )

    crew = Crew(
        agents=[signal_analyst, risk_adjudicator],
        tasks=[analyze_task, adjudicate_task],
        process=Process.sequential,  # Analyst runs first, then Adjudicator, in order
        verbose=False,
    )

    return crew


def _format_fraud_report(raw_answer: str, signal_text: str) -> str:
    """Post-process raw CrewAI output into a professional fraud report."""
    decision = ""
    reasoning = ""

    for line in raw_answer.split("\n"):
        if line.upper().startswith("DECISION:"):
            decision = line.split(":", 1)[1].strip()
        elif line.upper().startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

    if not decision:
        # Fallback: return raw if parsing fails
        return raw_answer

    # Map decision to emoji + label
    decision_upper = decision.upper()
    if "REJECT" in decision_upper:
        badge = "🚨 REJECTED"
    elif "HOLD" in decision_upper or "REVIEW" in decision_upper:
        badge = "⚠️ HOLD FOR REVIEW"
    else:
        badge = "✅ APPROVED"

    # Parse signal data for the summary section
    signal_lines = []
    for sig_line in signal_text.split("\n"):
        sig_line = sig_line.strip()
        if "velocity_flag" in sig_line or "velocity_count" in sig_line:
            parts = sig_line.split("(")
            val = "True" in sig_line or "true" in sig_line
            count = sig_line.split("found ")[-1].split(" orders")[0] if "found" in sig_line else "?"
            signal_lines.append(f"  ⚡ {'Velocity Check' if val else 'No Velocity Issue'}: {count} nearby orders")
        elif "country_mismatch" in sig_line:
            val = "True" in sig_line or "true" in sig_line
            signal_lines.append(f"  🌍 {'Country Mismatch Detected' if val else 'Countries Match'}")
        elif "new_account_high_value" in sig_line:
            val = "True" in sig_line or "true" in sig_line
            signal_lines.append(f"  👤 {'New Account + High Value' if val else 'Account Looks Normal'}")
        elif "disposable_email" in sig_line:
            val = "True" in sig_line or "true" in sig_line
            signal_lines.append(f"  📧 {'Disposable Email Detected' if val else 'Email Looks Legitimate'}")
        elif "TOTAL SIGNALS" in sig_line:
            triggered = sig_line.split(":")[-1].strip()
            signal_lines.append(f"\n  📊 Signals Triggered: {triggered}")

    report = (
        f"### 🛡️ Fraud Analysis Report\n\n"
        f"**Risk Decision:** {badge}\n\n"
        f"**Signal Breakdown:**\n" + "\n".join(signal_lines) + "\n\n"
        f"**Analysis:** {reasoning[:500]}"
    )
    return report


def _format_flag_summary(flagged: list[dict]) -> str:
    """Format the general sweep results into a clean table."""
    lines = ["### 🔍 Fraud Sweep Results\n"]
    for s in flagged:
        severity = "🚨 HIGH" if s["total_flags"] >= 3 else "⚠️ MEDIUM"
        lines.append(f"- {severity} — **{s['order_id']}**: {s['total_flags']}/4 signals triggered")
    lines.append("\n*Run a specific order ID through me for a full analysis.*")
    return "\n".join(lines)


def format_signal_data(signals: dict) -> str:
    """Turns the raw MCP tool output into readable text for the crew."""
    return (
        f"Order ID: {signals['order_id']}\n"
        f"- Multiple orders in short time window: {signals['velocity_flag']} "
        f"(found {signals['velocity_count']} orders nearby)\n"
        f"- Shipping/billing country mismatch: {signals['country_mismatch']}\n"
        f"- New account placing high-value order: {signals['new_account_high_value']}\n"
        f"- Disposable-looking email: {signals['disposable_email']}\n"
        f"- TOTAL SIGNALS TRIGGERED: {signals['total_flags']} out of 4"
    )


def run_fraud_agent(user_query: str) -> dict:
    """
    Main entry point -- called by the Supervisor.
    Handles two cases: a specific order ID mentioned, or a general
    "any suspicious orders?" sweep.
    """
    order_id = extract_order_id(user_query)

    if order_id:
        signals = call_tool("get_fraud_signals", order_id=order_id)
        if signals is None:
            return {
                "agent": "Fraud Detection Agent (CrewAI)",
                "answer": f"Order {order_id} was not found in our records.",
                "context_used": "",
            }

        signal_text = format_signal_data(signals)
        crew = build_fraud_crew(signal_text, order_id)
        raw_result = crew.kickoff()

        return {
            "agent": "Fraud Detection Agent (CrewAI: Signal Analyst -> Risk Adjudicator)",
            "answer": _format_fraud_report(str(raw_result), signal_text),
            "context_used": signal_text,
        }

    else:
        # General sweep -- no CrewAI needed here, this is a direct data query
        flagged = call_tool("get_all_flagged_orders")
        if not flagged:
            answer = "No orders in the current dataset triggered 2 or more fraud signals."
        else:
            answer = _format_flag_summary(flagged)

        return {
            "agent": "Fraud Detection Agent",
            "answer": answer,
            "context_used": str(flagged),
        }


if __name__ == "__main__":
    test_queries = ["Check order O2004 for fraud", "Are there any suspicious orders?"]
    for q in test_queries:
        print(f"\n--- Query: {q} ---")
        result = run_fraud_agent(q)
        print(f"Agent: {result['agent']}")
        print(f"Answer: {result['answer']}")
