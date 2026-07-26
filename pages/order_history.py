"""Order History page — view past orders and their status."""
import streamlit as st

from commerceos.database.connection import get_session
from commerceos.database.models import Customer, FraudSignal, Order, OrderItem, Product
from ui.components import status_badge
from ui.styling import inject_custom_css

st.set_page_config(page_title="Order History", page_icon="📦", layout="wide")
inject_custom_css()
st.title("📦 Order History")

email_query = st.text_input("Enter your email to look up orders",
                            placeholder="sarah@email.com")

if not email_query:
    st.info("👋 Enter your email address above to see your order history.")
    st.stop()

session = get_session()
customers = session.query(Customer).filter(Customer.email == email_query).all()

if not customers:
    st.warning(f"No customers found with email: {email_query}")
    session.close()
    st.stop()

orders = session.query(Order).filter(
    Order.customer_id.in_([c.id for c in customers])
).order_by(Order.created_at.desc()).all()

if not orders:
    st.info("No orders found. Start shopping on the Home page!")
    session.close()
    st.stop()

st.success(f"Found {len(orders)} order(s) for {email_query}")

for order in orders:
    customer = next((c for c in customers if c.id == order.customer_id), None)
    items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    with st.expander(
        f"**{order.id}** — ${order.total_amount:.2f} — "
        f"{status_badge(order.status)} — "
        f"{order.created_at.strftime('%b %d, %Y') if order.created_at else ''}",
        expanded=False
    ):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Items:**")
            for item in items:
                product = session.query(Product).filter(Product.id == item.product_id).first()
                pname = product.name if product else item.product_id
                st.write(f"- {pname} × {item.quantity} @ ${item.unit_price:.2f}")
        with col2:
            st.markdown(f"**Status:** {status_badge(order.status)}", unsafe_allow_html=True)
            if order.tracking_number:
                st.markdown(f"**Tracking:** `{order.tracking_number}`")
            st.markdown(f"**Shipping:** {order.shipping_address}")
            st.markdown(f"**Payment:** {order.payment_method}")

        # Fraud results
        fraud_results = session.query(FraudSignal).filter(
            FraudSignal.order_id == order.id, FraudSignal.decision.isnot(None)
        ).all()
        if fraud_results:
            final = fraud_results[-1].decision
            icon = "🛡️" if final == "APPROVE" else ("⚠️" if "HOLD" in final else "🚨")
            st.markdown(f"**Fraud Check:** {icon} {final}")

session.close()
