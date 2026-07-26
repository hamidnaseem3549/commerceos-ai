"""Admin Operations Dashboard — fraud alerts, stock overview, agent activity."""
import os
from datetime import UTC, datetime

import streamlit as st

from commerceos.agents.pricing_agent import analyze_and_apply_sales
from commerceos.database.connection import get_session
from commerceos.database.models import AgentLog, Alert, Order, Product
from commerceos.mcp.tools import call_tool
from ui.components import format_uptime, metric_card
from ui.styling import inject_custom_css

st.set_page_config(page_title="Admin Dashboard", page_icon="⚙️", layout="wide")
inject_custom_css()

if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    st.title("⚙️ Admin Dashboard")
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if not admin_password:
        st.error("ADMIN_PASSWORD environment variable not set. Add it to your .env file.")
        st.info("Copy `.env.example` to `.env` and set `ADMIN_PASSWORD`.")
        st.stop()
    pw = st.text_input("Enter admin password", type="password")
    if pw == admin_password:
        st.session_state.admin_authed = True
        st.rerun()
    elif pw:
        st.error("Incorrect password")
    st.info("🔒 Set `ADMIN_PASSWORD` in your `.env` file.")
    st.stop()

st.title("⚙️ Operations Dashboard")
st.caption("Real-time system overview for store operators")
st.sidebar.success("🔓 Admin mode active")

session = get_session()

# ── Quick Stats ──
total_orders = session.query(Order).count()
pending_orders = session.query(Order).filter(Order.status == "pending").count()
low_stock_count = session.query(Product).filter(
    Product.stock_quantity <= Product.reorder_threshold
).count()
fraud_alerts = session.query(Alert).filter(
    Alert.type == "fraud_flag", Alert.resolved == False
).count()

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Orders", total_orders)
with col2:
    metric_card("Pending", pending_orders)
with col3:
    metric_card("Low Stock", low_stock_count,
                delta="⚠️ Needs restock" if low_stock_count > 0 else "")
with col4:
    metric_card("Fraud Alerts", fraud_alerts,
                delta="🚨 Active" if fraud_alerts > 0 else "")
st.caption(f"🕐 Uptime: {format_uptime()} | {datetime.now(UTC).strftime('%H:%M:%S')} UTC")

st.divider()

# ── Fraud Alerts ──
st.subheader("🚨 Recent Fraud Alerts")
fraud_rows = session.query(Alert).filter(
    Alert.type == "fraud_flag"
).order_by(Alert.created_at.desc()).limit(10).all()

if fraud_rows:
    for alert in fraud_rows:
        severity_color = "#ef4444" if alert.severity == "HIGH" else "#f59e0b"
        st.markdown(
            f'<div style="padding:0.5rem 1rem;border-left:4px solid {severity_color};'
            f'background:white;border-radius:8px;margin-bottom:0.5rem;">'
            f'<strong>[{alert.severity}]</strong> {alert.message[:200]} '
            f'<span style="color:#636e72;font-size:0.8rem;">'
            f'({alert.created_at.strftime("%b %d, %H:%M") if alert.created_at else ""})</span></div>',
            unsafe_allow_html=True)
else:
    st.info("No fraud alerts. System is clear.")

st.divider()

# ── Low Stock ──
st.subheader("📦 Low Stock Products")
low_stock = session.query(Product).filter(
    Product.stock_quantity <= Product.reorder_threshold
).all()
if low_stock:
    cols = st.columns(3)
    for i, p in enumerate(low_stock):
        with cols[i % 3], st.container(border=True):
                st.markdown(f"**{p.name}**")
                st.markdown(f"Stock: **{p.stock_quantity}** (threshold: {p.reorder_threshold})")
                sev = "🔴 CRITICAL" if p.stock_quantity == 0 else "🟡 LOW"
                st.markdown(f"Severity: {sev}")
else:
    st.success("✅ All products adequately stocked.")

st.divider()

# ── Agent Activity ──
st.subheader("📋 Recent Agent Activity")
logs = session.query(AgentLog).order_by(AgentLog.timestamp.desc()).limit(20).all()
if logs:
    for log in logs:
        level_icon = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "🚨"}.get(log.level, "ℹ️")
        ts = log.timestamp.strftime("%H:%M:%S") if log.timestamp else ""
        st.markdown(
            f'<div style="padding:0.3rem 0.8rem;border-bottom:1px solid #f0f0f0;font-size:0.85rem;">'
            f'<strong>{log.agent_name}</strong> {level_icon} {log.action}: '
            f'{log.detail[:120]} <span style="color:#636e72;">({ts})</span></div>',
            unsafe_allow_html=True)
else:
    st.info("No agent activity recorded yet.")

st.divider()

# ── Quick Actions ──
st.subheader("⚡ Quick Actions")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔍 Run Fraud Sweep", use_container_width=True):
        with st.spinner("Scanning all orders..."):
            flagged = call_tool("get_all_flagged_orders")
        if flagged:
            st.warning(f"Found {len(flagged)} flagged orders!")
            for f in flagged:
                st.write(f"- {f['order_id']}: {f['total_flags']}/4 signals")
        else:
            st.success("No suspicious orders found.")
with col2:
    if st.button("📊 Check Stock Levels", use_container_width=True):
        low = call_tool("get_low_stock_products")
        if low:
            st.warning(f"{len(low)} products below reorder threshold")
        else:
            st.success("Stock levels are healthy.")
with col3:
    if st.button("🏷️ Analyze Pricing", use_container_width=True):
        with st.spinner("Analyzing inventory..."):
            applied = analyze_and_apply_sales()
        if applied:
            st.success(f"Applied sales to: {', '.join(applied)}")
        else:
            st.info("All products already optimally priced.")

session.close()
