"""Fraud detection agent — CrewAI 2-role sequential crew."""
import logging

try:
    import crewai.llms.cache as _crew_cache
    _crew_cache.mark_cache_breakpoint = lambda msg: msg
except ImportError:
    pass

from crewai import LLM, Agent, Crew, Process, Task

from commerceos.agents.base import AgentResult, BaseAgent
from commerceos.config import settings
from commerceos.mcp.tools import call_tool

_logger = logging.getLogger(__name__)

groq_llm = LLM(model=f"groq/{settings.fraud_llm_model}", temperature=0.2)


def extract_order_id(text: str):
    words = text.replace("#", " ").replace(",", " ").split()
    for word in words:
        if word.upper().startswith("O") and word[1:].isdigit():
            return word.upper()
    return None


def format_signal_data(signals: dict) -> str:
    return (
        f"Order ID: {signals['order_id']}\n"
        f"- Velocity check ({signals['velocity_count']} nearby): {signals['velocity_flag']}\n"
        f"- Country mismatch: {signals['country_mismatch']}\n"
        f"- New account + high value: {signals['new_account_high_value']}\n"
        f"- Disposable email: {signals['disposable_email']}\n"
        f"- TOTAL SIGNALS: {signals['total_flags']}/4"
    )


class FraudAgent(BaseAgent):
    name = "fraud"
    description = "Analyzes orders for fraud signals using multi-agent crew"
    keywords = ["fraud", "suspicious", "scam", "fake", "fraudulent", "check order"]  # noqa: RUF012

    def run(self, query: str) -> AgentResult:
        order_id = extract_order_id(query)
        actions = [{"agent": "fraud", "action": "analyze", "detail": f"Order: {order_id or 'sweep'}"}]

        if order_id:
            signals = call_tool("get_fraud_signals", order_id=order_id)
            if signals is None:
                return AgentResult(answer=f"Order {order_id} not found.", agent="Fraud Detection Agent",
                                   ops_alert="", context_used="", actions=actions)

            signal_text = format_signal_data(signals)
            crew = self._build_crew(signal_text, order_id)
            raw_result = crew.kickoff()
            report = self._format_report(str(raw_result), signal_text)

            # Persist alert if flagged
            if "REJECT" in str(raw_result).upper() or "HOLD" in str(raw_result).upper():
                try:
                    from commerceos.database.connection import get_session
                    from commerceos.database.models import Alert
                    session = get_session()
                    alert = Alert(
                        type="fraud_flag",
                        severity="HIGH" if "REJECT" in str(raw_result).upper() else "MEDIUM",
                        message=f"Order {order_id}: flagged",
                        source_agent="Fraud Agent",
                    )
                    session.add(alert)
                    session.commit()
                    session.close()
                except Exception as e:  # noqa: BLE001
                    _logger.warning("Failed to persist fraud alert for %s: %s", order_id, e)

            return AgentResult(answer=report, agent="Fraud Detection Agent (CrewAI)",
                               ops_alert=report if "REJECT" in report else "",
                               context_used=signal_text, actions=actions)
        else:
            flagged = call_tool("get_all_flagged_orders")
            if not flagged:
                answer = "No orders triggered 2+ fraud signals."
            else:
                lines = ["### 🔍 Fraud Sweep Results\n"]
                for s in flagged:
                    sev = "🚨 HIGH" if s["total_flags"] >= 3 else "⚠️ MEDIUM"
                    lines.append(f"- {sev} — {s['order_id']}: {s['total_flags']}/4 signals")
                answer = "\n".join(lines)
            return AgentResult(answer=answer, agent="Fraud Detection Agent",
                               ops_alert="", context_used=str(flagged), actions=actions)

    def _build_crew(self, signal_text: str, order_id: str):
        analyst = Agent(
            role="Fraud Signal Analyst",
            goal="Objectively interpret raw fraud signals",
            backstory="Data analyst at e-commerce trust & safety team.",
            llm=groq_llm, verbose=False,
        )
        adjudicator = Agent(
            role="Risk Adjudicator",
            goal="Make final risk decision: APPROVE, HOLD, or REJECT",
            backstory="Senior fraud risk manager.",
            llm=groq_llm, verbose=False,
        )
        analyze = Task(
            description=f"Raw signals for {order_id}:\n{signal_text}\n\nInterpret neutrally.",
            expected_output="Factual interpretation of signals.",
            agent=analyst,
        )
        adjudicate = Task(
            description="Based on the Signal Analyst's interpretation, make final decision.\n"
                        "Format:\nDECISION: [APPROVE / HOLD FOR REVIEW / REJECT]\nREASONING: ...",
            expected_output="Decision with reasoning.",
            agent=adjudicator,
            context=[analyze],
        )
        return Crew(agents=[analyst, adjudicator], tasks=[analyze, adjudicate],
                    process=Process.sequential, verbose=False)

    def _format_report(self, raw: str, signal_text: str) -> str:
        decision, reasoning = "", ""
        for line in raw.split("\n"):
            if line.upper().startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip()
            elif line.upper().startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
        if not decision:
            return raw
        du = decision.upper()
        badge = "🚨 REJECTED" if "REJECT" in du else ("⚠️ HOLD FOR REVIEW" if "HOLD" in du or "REVIEW" in du else "✅ APPROVED")
        return f"### 🛡️ Fraud Analysis Report\n\n**Risk Decision:** {badge}\n\n**Signal Breakdown:**\n{signal_text}\n\n**Analysis:** {reasoning[:500]}"
