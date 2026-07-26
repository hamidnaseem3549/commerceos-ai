"""
pages/cart.py — Cart view with full checkout and event emission.
"""
import streamlit as st

from commerceos.mcp.tools import call_tool
from ui.styling import inject_custom_css

st.set_page_config(page_title="Cart & Checkout", page_icon="🛒", layout="wide")
inject_custom_css()
st.title("🛒 Your Cart")

if "cart" not in st.session_state:
    st.session_state.cart = {}
if "_order_placed" not in st.session_state:
    st.session_state._order_placed = False
if "_last_order" not in st.session_state:
    st.session_state._last_order = {}

# ── Show post-checkout success ──
if st.session_state._order_placed:
    st.balloons()
    order_info = st.session_state._last_order
    st.success(
        f"✅ **Order {order_info.get('order_id', '')} placed!** Thank you, "
        f"{order_info.get('customer_name', '')}.\n\n"
        f"💡 Try asking the **AI Assistant** to check your order for fraud!"
    )
    st.info("📦 Go to **Order History** (sidebar) to track your orders.")
    st.session_state._order_placed = False
    st.session_state.cart = {}
    st.page_link("pages/AI_Assistant.py", label="→ Go to AI Assistant", icon="🤖")
    st.stop()

if not st.session_state.cart:
    st.info("Your cart is empty. Go to the Home page to browse products.")
    st.stop()

# ── Cart items ──
subtotal = 0.0
cart_data = []

for product_id, qty in list(st.session_state.cart.items()):
    product = call_tool("get_product_by_id", product_id=product_id)
    if product is None:
        continue
    price = product.get("sale_price", product["price"]) if product.get("is_on_sale") else product["price"]
    line_total = price * qty
    subtotal += line_total
    cart_data.append({"product": product, "qty": qty, "price": price})

    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        sale_tag = " 🏷️ **ON SALE!**" if product.get("is_on_sale") else ""
        st.write(f"**{product['product_name']}**{sale_tag}")
    with col2:
        st.write(f"${price:.2f} each")
    with col3:
        new_qty = st.number_input("Qty", min_value=0, max_value=20, value=qty,
                                  key=f"qty_{product_id}", label_visibility="collapsed")
        if new_qty != qty:
            if new_qty == 0:
                del st.session_state.cart[product_id]
            else:
                st.session_state.cart[product_id] = new_qty
            st.rerun()
    with col4:
        st.write(f"${line_total:.2f}")

st.divider()
tax = round(subtotal * 0.08, 2)
total = round(subtotal + tax, 2)

st.markdown("### Order Summary")
col1, col2 = st.columns([3, 1])
with col1:
    st.write(f"**Subtotal ({sum(st.session_state.cart.values())} items):**")
    st.write("**Estimated Tax (8%):**")
    st.markdown("### **Total:**")
with col2:
    st.write(f"**${subtotal:.2f}**")
    st.write(f"**${tax:.2f}**")
    st.markdown(f"### **${total:.2f}**")

# ── Checkout form ──
st.subheader("Checkout")
with st.form("checkout_form", clear_on_submit=True):
    name = st.text_input("Full Name", placeholder="Sarah Ahmed")
    email = st.text_input("Email", placeholder="sarah@email.com")
    country = st.text_input("Shipping Country", placeholder="Pakistan")
    placed = st.form_submit_button("Place Order", type="primary")

    if placed:
        if not name or not email or not country:
            st.error("Please fill in all checkout fields.")
        else:
            first_pid = next(iter(st.session_state.cart.keys()))
            first_qty = st.session_state.cart[first_pid]

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
                # Event bus auto-triggers fraud check + inventory deduction
                st.session_state._last_order = {
                    "order_id": order["order_id"],
                    "customer_name": name,
                    "customer_email": email,
                }
                st.session_state._order_placed = True
                st.rerun()

st.sidebar.caption("Need help? Visit the AI Assistant page.")
