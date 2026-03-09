"""
styles.py — Premium dark CSS for the AI Coach Companion.
Clean typography, minimal borders, floating chat panel.
"""

MAIN_CSS = """
<style>
    /* -- Global ---------------------------------------- */
    .stApp {
        background-color: #0a0a0a;
        color: #e0e0e0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* -- Headers ---------------------------------------- */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 400 !important;
        letter-spacing: -0.02em;
        font-family: 'Inter', sans-serif !important;
    }

    /* -- Main Title ------------------------------------- */
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

    /* -- Chat Bubbles ----------------------------------- */
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

    /* -- Emotion Tag ------------------------------------ */
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

    /* -- Metric Cards ----------------------------------- */
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

    /* -- Entity Cards ----------------------------------- */
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

    /* -- Goal Cards -------------------------------------- */
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

    /* -- Progress Bar ----------------------------------- */
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

    /* -- Section Divider -------------------------------- */
    .section-divider {
        border: none;
        border-top: 1px solid #1a1a1a;
        margin: 2rem 0;
    }

    /* -- Sidebar ---------------------------------------- */
    section[data-testid="stSidebar"] {
        background-color: #060606;
        border-right: 1px solid #151515;
    }

    /* -- Tab Styling ------------------------------------ */
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

    /* -- Input Styling ---------------------------------- */
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

    /* -- Button Styling --------------------------------- */
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

    /* -- Selectbox / Slider ------------------------------ */
    .stSelectbox > div > div {
        background-color: #111111 !important;
        border: 1px solid #2a2a2a !important;
    }

    /* -- Hide Streamlit Branding ------------------------- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* -- Onboarding ------------------------------------- */
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

    /* -- Checkin Cards ----------------------------------- */
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

    /* ================================================== */
    /* -- FLOATING CHAT PANEL ---------------------------- */
    /* ================================================== */

    /* Floating trigger button - bottom right */
    .chat-fab {
        position: fixed;
        bottom: 28px;
        right: 28px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: #fff;
        color: #000;
        border: none;
        cursor: pointer;
        z-index: 9998;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 24px rgba(0,0,0,0.5);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.02em;
    }
    .chat-fab:hover {
        transform: scale(1.08);
        box-shadow: 0 6px 32px rgba(0,0,0,0.7);
    }

    /* Notification dot on FAB */
    .chat-fab-dot {
        position: absolute;
        top: 4px;
        right: 4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #ff3b30;
        border: 2px solid #0a0a0a;
    }

    /* The panel itself */
    .chat-panel {
        position: fixed;
        bottom: 96px;
        right: 28px;
        width: 380px;
        height: 520px;
        background: #0c0c0c;
        border: 1px solid #1e1e1e;
        border-radius: 16px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        box-shadow: 0 12px 48px rgba(0,0,0,0.6);
        animation: panelSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    @keyframes panelSlideUp {
        from {
            opacity: 0;
            transform: translateY(20px) scale(0.96);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    /* Panel header */
    .chat-panel-header {
        padding: 16px 18px 12px 18px;
        border-bottom: 1px solid #1a1a1a;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0c0c0c;
        flex-shrink: 0;
    }
    .chat-panel-title {
        color: #fff;
        font-size: 0.95rem;
        font-weight: 500;
        margin: 0;
        letter-spacing: -0.01em;
    }
    .chat-panel-subtitle {
        color: #555;
        font-size: 0.7rem;
        margin: 2px 0 0 0;
        font-weight: 300;
    }
    .chat-panel-close {
        background: transparent;
        border: none;
        color: #555;
        font-size: 1.1rem;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 6px;
        transition: color 0.15s ease, background 0.15s ease;
        font-family: 'Inter', sans-serif;
    }
    .chat-panel-close:hover {
        color: #fff;
        background: #1a1a1a;
    }

    /* Panel message area */
    .chat-panel-messages {
        flex: 1;
        overflow-y: auto;
        padding: 14px 16px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    /* Scrollbar styling */
    .chat-panel-messages::-webkit-scrollbar {
        width: 3px;
    }
    .chat-panel-messages::-webkit-scrollbar-track {
        background: transparent;
    }
    .chat-panel-messages::-webkit-scrollbar-thumb {
        background: #2a2a2a;
        border-radius: 3px;
    }

    /* Messages inside the panel */
    .panel-msg-coach {
        background: #111;
        border-left: 2px solid #fff;
        border-radius: 10px 10px 10px 2px;
        padding: 11px 14px;
        color: #ccc;
        font-size: 0.88rem;
        line-height: 1.55;
        font-weight: 300;
        max-width: 92%;
    }
    .panel-msg-user {
        background: #1a1a1a;
        border: 1px solid #252525;
        border-radius: 10px 10px 2px 10px;
        padding: 9px 14px;
        color: #e0e0e0;
        font-size: 0.88rem;
        line-height: 1.5;
        max-width: 85%;
        margin-left: auto;
    }

    /* Panel quick reply buttons */
    .panel-replies {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        padding: 0 16px 6px 16px;
        flex-shrink: 0;
    }
    .panel-reply-btn {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        color: #ccc;
        padding: 7px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.15s ease;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        letter-spacing: 0.01em;
    }
    .panel-reply-btn:hover {
        background: #252525;
        border-color: #444;
        color: #fff;
    }

    /* Panel input area */
    .chat-panel-input {
        padding: 10px 14px 14px 14px;
        border-top: 1px solid #1a1a1a;
        background: #0c0c0c;
        flex-shrink: 0;
    }

    /* -- Coach Insight Card (inside panel) -------------- */
    .coach-insight {
        background: linear-gradient(135deg, #111 0%, #0d0d0d 100%);
        border: 1px solid #1e1e1e;
        border-left: 3px solid #fff;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 6px 0;
    }
    .coach-insight-type {
        color: #555;
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 0 0 6px 0;
    }
    .coach-insight-text {
        color: #ddd;
        font-size: 0.88rem;
        line-height: 1.55;
        margin: 0;
        font-weight: 300;
    }

    /* -- Session Summary Card --------------------------- */
    .session-summary {
        background: #0f0f0f;
        border: 1px solid #1e1e1e;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 8px 0;
    }
    .session-summary-title {
        color: #888;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 0 0 8px 0;
    }
    .session-summary-item {
        color: #ccc;
        font-size: 0.85rem;
        margin: 4px 0;
        padding-left: 12px;
        border-left: 2px solid #333;
        font-weight: 300;
    }

</style>
"""
