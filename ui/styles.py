"""
styles.py — Premium dark CSS for the AI Coach Companion.
No emojis, clean typography, minimal borders.
"""

MAIN_CSS = """
<style>
    /* ── Global ──────────────────────────────────── */
    .stApp {
        background-color: #0a0a0a;
        color: #e0e0e0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Headers ─────────────────────────────────── */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 400 !important;
        letter-spacing: -0.02em;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Main Title ──────────────────────────────── */
    .app-title {
        font-size: 2.2rem;
        font-weight: 300;
        color: #ffffff;
        margin-bottom: 0;
        letter-spacing: -0.03em;
    }
    .app-subtitle {
        font-size: 0.9rem;
        color: #666666;
        margin-top: 4px;
        margin-bottom: 1.5rem;
        font-weight: 300;
        letter-spacing: 0.02em;
    }

    /* ── Chat Bubbles ────────────────────────────── */
    .chat-user {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px 12px 4px 12px;
        padding: 14px 18px;
        margin: 8px 0;
        color: #e0e0e0;
        font-size: 0.95rem;
        line-height: 1.5;
        max-width: 85%;
        margin-left: auto;
    }
    .chat-coach {
        background: #0f0f0f;
        border: 1px solid #1e1e1e;
        border-left: 2px solid #ffffff;
        border-radius: 12px 12px 12px 4px;
        padding: 14px 18px;
        margin: 8px 0;
        color: #d0d0d0;
        font-size: 0.95rem;
        line-height: 1.6;
        max-width: 85%;
        font-weight: 300;
    }

    /* ── Emotion Tag ─────────────────────────────── */
    .emotion-tag {
        display: inline-block;
        background: transparent;
        border: 1px solid #333333;
        color: #999999;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-top: 4px;
    }
    .emotion-tag-strong {
        border-color: #ffffff;
        color: #ffffff;
    }

    /* ── Metric Cards ────────────────────────────── */
    .metric-card {
        background: #0f0f0f;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 300;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #555555;
        margin: 4px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* ── Entity Cards ────────────────────────────── */
    .entity-card {
        background: #0f0f0f;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 8px;
    }
    .entity-name {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 500;
        margin: 0;
    }
    .entity-type {
        color: #555555;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 2px 0 0 0;
    }
    .entity-detail {
        color: #888888;
        font-size: 0.85rem;
        margin: 6px 0 0 0;
        font-weight: 300;
    }

    /* ── Goal Cards ───────────────────────────────── */
    .goal-card {
        background: #0f0f0f;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 8px;
    }
    .goal-title {
        color: #ffffff;
        font-size: 0.95rem;
        font-weight: 500;
        margin: 0;
    }
    .goal-progress {
        color: #888888;
        font-size: 0.8rem;
        margin: 4px 0 0 0;
    }

    /* ── Progress Bar ─────────────────────────────── */
    .progress-bar-bg {
        background: #1a1a1a;
        border-radius: 4px;
        height: 6px;
        margin: 8px 0;
        overflow: hidden;
    }
    .progress-bar-fill {
        background: #ffffff;
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    /* ── Section Divider ──────────────────────────── */
    .section-divider {
        border: none;
        border-top: 1px solid #1a1a1a;
        margin: 2rem 0;
    }

    /* ── Sidebar ──────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #060606;
        border-right: 1px solid #151515;
    }

    /* ── Tab Styling ──────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #1a1a1a;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        color: #666666;
        font-weight: 400;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #ffffff !important;
        background: transparent !important;
    }

    /* ── Input Styling ────────────────────────────── */
    .stTextInput > div > div > input {
        background-color: #111111 !important;
        border: 1px solid #2a2a2a !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #ffffff !important;
        box-shadow: none !important;
    }
    .stTextArea > div > div > textarea {
        background-color: #111111 !important;
        border: 1px solid #2a2a2a !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
    }

    /* ── Button Styling ───────────────────────────── */
    .stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.02em !important;
        padding: 8px 24px !important;
        transition: opacity 0.2s ease !important;
    }
    .stButton > button:hover {
        opacity: 0.85 !important;
    }

    /* ── Selectbox / Slider ────────────────────────── */
    .stSelectbox > div > div {
        background-color: #111111 !important;
        border: 1px solid #2a2a2a !important;
    }

    /* ── Hide Streamlit Branding ──────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Onboarding ───────────────────────────────── */
    .onboard-header {
        font-size: 1.8rem;
        font-weight: 300;
        color: #ffffff;
        text-align: center;
        margin: 3rem 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .onboard-sub {
        font-size: 0.95rem;
        color: #666666;
        text-align: center;
        margin: 0 0 2rem 0;
        font-weight: 300;
    }
    .onboard-label {
        color: #888888;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }

    /* ── Checkin Cards ────────────────────────────── */
    .checkin-card {
        background: #0f0f0f;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .streak-number {
        font-size: 3rem;
        font-weight: 300;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.03em;
    }
    .streak-label {
        font-size: 0.7rem;
        color: #555555;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
</style>
"""
