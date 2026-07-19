"""
app.py

PURPOSE:
Main entry point for the CommerceOS storefront. This is the "Home/Browse"
page. Streamlit auto-detects files in /pages and adds them as additional
pages in the sidebar navigation -- so this single app.py + pages/ folder
becomes a full multi-page storefront.

RUN WITH: streamlit run app.py
"""

import streamlit as st

from utils.styling import inject_custom_css


@st.cache_resource(show_spinner=False)
def _get_tool_layer():
    """
    Lazy-import the MCP tools module so pandas CSVs load once, not on every re-run.
    """
    from mcp_server.tools import call_tool as _ct
    return _ct


call_tool = _get_tool_layer()

st.set_page_config(page_title="Urban Thread Co.", page_icon="🛍️", layout="wide")
inject_custom_css()

# Session state holds the cart -- persists as the user navigates between pages
if "cart" not in st.session_state:
    st.session_state.cart = {}  # {product_id: quantity}

if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())[:8]  # unique session for LangGraph memory

st.title("🛍️ Urban Thread Co.")
st.caption("Powered by CommerceOS AI — an autonomous multi-agent operations system")

st.divider()

# --- Product Grid ---
st.subheader("Shop Our Collection")

search_query = st.text_input("🔍 Search products", placeholder="e.g. shoes, t-shirt, watch")

if search_query:
    products = call_tool("search_products", query=search_query)
else:
    products = call_tool("get_all_products")

if not products:
    st.info("No products matched your search.")
else:
    cols = st.columns(4)
    for idx, product in enumerate(products):
        with cols[idx % 4]:
            with st.container(border=True):
                st.markdown(f"**{product['product_name']}**")
                st.caption(product["category"])
                st.markdown(f"### ${product['price']}")

                if product["stock_quantity"] == 0:
                    st.markdown("<span class='stock-badge out-of-stock'>Out of Stock</span>", unsafe_allow_html=True)
                elif product["stock_quantity"] <= product["reorder_threshold"]:
                    st.markdown(f"<span class='stock-badge low-stock'>Only {product['stock_quantity']} left!</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span class='stock-badge in-stock'>{product['stock_quantity']} in stock</span>", unsafe_allow_html=True)

                if product["stock_quantity"] > 0:
                    if st.button("Add to Cart", key=f"add_{product['product_id']}"):
                        pid = product["product_id"]
                        st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + 1
                        st.toast(f"Added {product['product_name']} to cart!")
                        st.rerun()

st.divider()
cart_count = sum(st.session_state.cart.values())
st.sidebar.metric("🛒 Cart Items", cart_count)
st.sidebar.caption("Use the sidebar to navigate to Cart/Checkout or the AI Assistant.")
