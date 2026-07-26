"""Reusable Streamlit UI components."""
from datetime import UTC, datetime

import streamlit as st


def metric_card(label: str, value, delta="", help_text=""):
    delta_html = f'<div style="font-size:0.75rem;color:#e94560;">{delta}</div>' if delta else ""
    st.markdown(
        f'<div style="background:white;padding:1rem;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);text-align:center;">'
        f'<div style="font-size:0.8rem;color:#636e72;text-transform:uppercase;font-weight:600;">{label}</div>'
        f'<div style="font-size:1.8rem;font-weight:700;color:#1a1a2e;margin:0.5rem 0;">{value}</div>'
        f'{delta_html}</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    colors = {"pending": "#f59e0b", "confirmed": "#3b82f6", "processing": "#636e72",
              "shipped": "#8b5cf6", "delivered": "#10b981", "cancelled": "#ef4444"}
    c = colors.get(status.lower(), "#636e72")
    return f'<span style="background:{c}20;color:{c};padding:0.2rem 0.6rem;border-radius:20px;font-size:0.8rem;font-weight:600;">{status.upper()}</span>'


def format_uptime() -> str:
    if "_startup" not in st.session_state:
        st.session_state._startup = datetime.now(UTC)
    delta = datetime.now(UTC) - st.session_state._startup
    h, r = divmod(int(delta.total_seconds()), 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"
