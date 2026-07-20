"""app.py — Urban Thread Co. storefront with category filter and product images."""
import streamlit as st
from ui.styling import inject_custom_css
from commerceos.mcp.tools import call_tool

st.set_page_config(page_title="Urban Thread Co.", page_icon="🛍️", layout="wide")
inject_custom_css()

if "cart" not in st.session_state:
    st.session_state.cart = {}
if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())[:8]
if "_category" not in st.session_state:
    st.session_state._category = "All"

st.title("🛍️ Urban Thread Co.")
st.caption("Powered by CommerceOS AI — autonomous multi-agent e-commerce operations")

# ── Category Filter ──
categories = ["All", "Apparel", "Electronics", "Accessories", "Home & Living",
              "Footwear", "Sports & Fitness"]
cols = st.columns(len(categories))
for i, cat in enumerate(categories):
    active = st.session_state._category == cat
    if cols[i].button(cat, key=f"cat_{cat}", type="primary" if active else "secondary", use_container_width=True):
        st.session_state._category = cat
        st.rerun()

# ── Search ──
search_query = st.text_input("🔍 Search products", placeholder="e.g. shoes, t-shirt, watch")

if search_query:
    products = call_tool("search_products", query=search_query)
else:
    products = call_tool("get_all_products")

# Filter by category
if st.session_state._category != "All":
    products = [p for p in products if p["category"] == st.session_state._category]

if not products:
    st.info("No products matched your search or filter.")
else:
    cols = st.columns(4)
    for idx, product in enumerate(products):
        with cols[idx % 4]:
            with st.container(border=True):
                # Product image
                img_path = f"ui/assets/images/product_{product['product_id'].lower()}.svg"
                try:
                    with open(img_path) as f:
                        svg_content = f.read()
                    st.markdown(f'<div style="border-radius: 8px; overflow: hidden;">{svg_content}</div>',
                                unsafe_allow_html=True)
                except FileNotFoundError:
                    st.markdown(f'<div style="height:100px;background:#f0f0f0;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#636e72;">{product["product_name"][0]}</div>',
                                unsafe_allow_html=True)

                # Sale badge
                if product.get("is_on_sale"):
                    st.markdown(f'<span style="background:#ff6b35;color:white;padding:0.2rem 0.5rem;border-radius:4px;font-size:0.7rem;font-weight:700;">SALE</span>',
                                unsafe_allow_html=True)

                st.markdown(f"**{product['product_name']}**")
                st.caption(product["category"])

                # Price
                if product.get("is_on_sale") and product.get("sale_price"):
                    st.markdown(f"### ~~${product['price']:.2f}~~ **${product['sale_price']:.2f}**")
                else:
                    st.markdown(f"### ${product['price']:.2f}")

                # Stock badge
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
st.sidebar.caption("Navigate via sidebar →")
