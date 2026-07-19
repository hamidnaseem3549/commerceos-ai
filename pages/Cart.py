"""
pages/cart.py

PURPOSE:
Cart and simulated checkout flow. Users can view cart, adjust quantities,
and place a real demo order. The order is appended to the in-memory
DataFrame via MCP tools layer so the Fraud Agent can immediately analyze
freshly placed orders — demonstrating the system reacting to live activity.
"""

import streamlit as st

from utils.styling import inject_custom_css


@st.cache_resource(show_spinner=False)
def _get_tool_layer():
    from mcp_server.tools import call_tool as _ct
    return _ct


call_tool = _get_tool_layer()

st.set_page_config(page_title="Cart & Checkout", page_icon="🛒", layout="wide")
inject_custom_css()
st.title("🛒 Your Cart")

# ── Session state ──
if "cart" not in st.session_state:
    st.session_state.cart = {}

if "_order_placed" not in st.session_state:
    st.session_state._order_placed = False

# ── Show post-checkout success if just placed ──
if st.session_state._order_placed:
    st.balloons()
    order_info = st.session_state.get("_last_order", {})
    st.success(
        f"✅ **Order {order_info.get('order_id', '')} placed!** Thank you, "
        f"{order_info.get('customer_name', '')}. A confirmation will be sent to "
        f"{order_info.get('customer_email', '')}.\n\n"
        f"💡 **Try this:** Go to the **AI Assistant** and ask "
        f"\"Check {order_info.get('order_id', '')} for fraud\" to see the "
        f"Fraud Agent analyze your freshly placed order!"
    )
    st.session_state._order_placed = False
    st.session_state.cart = {}
    st.page_link("pages/AI_Assistant.py", label="→ Go to AI Assistant", icon="🤖")
    st.stop()

# ── Empty cart state ──
if not st.session_state.cart:
    st.info("Your cart is empty. Go to the Home page to browse products.")
    st.stop()

# ── Cart items display ──
total = 0.0
for product_id, qty in list(st.session_state.cart.items()):
    product = call_tool("get_product_by_id", product_id=product_id)
    if product is None:
        continue

    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.write(f"**{product['product_name']}**")
    with col2:
        st.write(f"${product['price']} each")
    with col3:
        new_qty = st.number_input(
            "Qty", min_value=0, max_value=20, value=qty,
            key=f"qty_{product_id}", label_visibility="collapsed",
        )
        if new_qty != qty:
            if new_qty == 0:
                del st.session_state.cart[product_id]
            else:
                st.session_state.cart[product_id] = new_qty
            st.rerun()
    with col4:
        line_total = product["price"] * qty
        st.write(f"${line_total:.2f}")
    total += product["price"] * qty

st.divider()
st.markdown(f"### Total: ${total:.2f}")

# ── Checkout form (Enter key submits!) ──
st.subheader("Checkout")
with st.form("checkout_form", clear_on_submit=True):
    name = st.text_input("Full Name", placeholder="Sarah Ahmed")
    email = st.text_input("Email", placeholder="sarah@email.com")
    country = st.text_input("Shipping Country", placeholder="Pakistan")
    placed = st.form_submit_button("Place Order", type="primary")

    if placed:
        # Validate all fields — captured directly from return values (no race condition)
        if not name or not email or not country:
            st.error("Please fill in all checkout fields before placing your order.")
        else:
            # Pick the first product in the cart for the order
            first_pid = list(st.session_state.cart.keys())[0]
            first_qty = st.session_state.cart[first_pid]

            # Create a real traceable order via MCP tools
            order = call_tool("append_order",
                customer_name=name,
                customer_email=email,
                shipping_country=country,
                product_id=first_pid,
                quantity=first_qty,
            )

            if "error" in order:
                st.error(f"Could not place order: {order['error']}")
            else:
                # Store order info for display on rerun
                st.session_state._last_order = {
                    "order_id": order["order_id"],
                    "customer_name": name,
                    "customer_email": email,
                }
                st.session_state._order_placed = True
                st.rerun()

st.sidebar.caption("Need help with an order? Visit the AI Assistant page.")
