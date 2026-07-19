"""
utils/styling.py

PURPOSE:
Shared styling for the CommerceOS storefront. Provides a single function
to inject consistent Urban Thread Co. branding, colors, and layout across
all Streamlit pages. Import and call inject_custom_css() once per page.
"""

import streamlit as st


def inject_custom_css():
    """Inject Urban Thread Co. brand styling into the current page."""
    st.markdown("""
    <style>
        /* ── Brand Colors ── */
        :root {
            --utc-primary: #1a1a2e;
            --utc-accent: #e94560;
            --utc-gold: #f5c518;
            --utc-light: #f8f9fa;
            --utc-card-bg: #ffffff;
            --utc-text: #2d3436;
            --utc-muted: #636e72;
        }

        /* ── Global Reset & Typography ── */
        .stApp {
            background-color: var(--utc-light);
        }
        h1, h2, h3 {
            color: var(--utc-primary);
            font-family: 'Segoe UI', -apple-system, sans-serif;
        }
        h1 {
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        h2 {
            font-weight: 600;
        }

        /* ── Product Cards ── */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            background: var(--utc-card-bg);
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }

        /* ── Buttons ── */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.15s ease;
        }
        div.stButton > button[kind="primary"] {
            background: var(--utc-accent);
            color: white;
            border: none;
        }
        div.stButton > button[kind="primary"]:hover {
            background: #d63850;
            box-shadow: 0 4px 12px rgba(233, 69, 96, 0.3);
        }

        /* ── Chat Bubbles in AI Assistant ── */
        .chat-message {
            padding: 0.75rem 1rem;
            border-radius: 12px;
            margin-bottom: 0.75rem;
            line-height: 1.5;
        }
        .chat-message.user {
            background: #e8f4fd;
            border-left: 4px solid #3498db;
        }
        .chat-message.agent {
            background: #f0fdf4;
            border-left: 4px solid #2ecc71;
        }
        .chat-message.error {
            background: #fef2f2;
            border-left: 4px solid #ef4444;
        }
        .chat-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--utc-muted);
            margin-bottom: 0.25rem;
        }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background: #ffffff !important;
            border-right: 1px solid #e9ecef;
        }
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] .st-emotion-cache-1aehpvj,
        section[data-testid="stSidebar"] .st-emotion-cache-1aehpvj p,
        section[data-testid="stSidebar"] .st-emotion-cache-1aehpvj span,
        section[data-testid="stSidebar"] .st-emotion-cache-1wbqy5l span,
        section[data-testid="stSidebar"] .st-emotion-cache-1aehpvj a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] div,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li,
        section[data-testid="stSidebar"] .st-emotion-cache-1wbqy5l,
        section[data-testid="stSidebar"] .st-emotion-cache-15zrgzn,
        section[data-testid="stSidebar"] .st-emotion-cache-15zrgzn span {
            color: var(--utc-primary) !important;
        }
        /* Sidebar navigation links */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            font-weight: 500;
            text-decoration: none;
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            transition: all 0.15s ease;
            display: block;
            margin: 0.1rem 0;
            color: var(--utc-primary) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background: #f0f2f6;
            color: var(--utc-accent) !important;
        }
        /* Active/highlighted nav item */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: #fef0f2;
            color: var(--utc-accent) !important;
            font-weight: 600;
            border-left: 3px solid var(--utc-accent);
        }
        /* Brand logo area at top of sidebar */
        section[data-testid="stSidebar"]::before {
            content: "🛍️ Urban Thread Co.";
            display: block;
            padding: 1rem 1rem 0.5rem;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--utc-primary);
            border-bottom: 1px solid #e9ecef;
            margin-bottom: 0.5rem;
        }
        /* Sidebar collapse button */
        section[data-testid="stSidebar"] button {
            color: var(--utc-muted) !important;
        }
        section[data-testid="stSidebar"] button:hover {
            color: var(--utc-primary) !important;
        }
        /* Sidebar divider */
        section[data-testid="stSidebar"] hr {
            border-color: #e9ecef;
        }
        /* Sidebar labels and captions */
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] .stMarkdown p {
            color: var(--utc-muted) !important;
        }
        section[data-testid="stSidebar"] .stMetric label {
            color: var(--utc-muted) !important;
        }
        section[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] {
            color: var(--utc-primary) !important;
            font-weight: 700;
        }

        /* ── Dividers ── */
        hr {
            margin: 1.5rem 0;
            border-color: rgba(0,0,0,0.08);
        }

        /* ── Spinner Styling ── */
        .stSpinner > div {
            border-top-color: var(--utc-accent) !important;
        }

        /* ── Info / Success / Error Boxes ── */
        div[data-testid="stAlert"] {
            border-radius: 8px;
            border-left-width: 4px;
        }

        /* ── Expander ── */
        div.streamlit-expanderHeader {
            font-weight: 600;
            color: var(--utc-primary);
        }

        /* ── Cart Checkout Form ── */
        div[data-testid="stForm"] {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }

        /* ── Product Badges ── */
        .stock-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .stock-badge.in-stock {
            background: #d4edda;
            color: #155724;
        }
        .stock-badge.low-stock {
            background: #fff3cd;
            color: #856404;
        }
        .stock-badge.out-of-stock {
            background: #f8d7da;
            color: #721c24;
        }

        /* ── Responsive Tweaks ── */
        @media (max-width: 768px) {
            div[data-testid="column"] {
                min-width: 100% !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)
