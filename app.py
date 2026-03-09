"""
app.py — AI Coach Companion: Main Streamlit Application
Side-panel chat + Dashboard tabs in a native split layout.
Coach leads the conversation. User just listens and acts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
from datetime import datetime

from ui.styles import MAIN_CSS
from agents.orchestrator import Orchestrator
from config import COACHING_MODES, TONE_INSTRUCTIONS
from squad_server import start_server as start_squad_server, is_running as squad_running
from squad_client import SquadClient

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="AI Companion",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject CSS
st.markdown(MAIN_CSS, unsafe_allow_html=True)

# --------------------------------------------------
# Initialize Orchestrator (cached)
# --------------------------------------------------
@st.cache_resource
def get_orchestrator():
    return Orchestrator()

orch = get_orchestrator()

# --------------------------------------------------
# Session State
# --------------------------------------------------
if "chat_messages" not in st.session_state:
    db_messages = orch.db.get_recent_messages(50)
    loaded = []
    for msg in db_messages:
        entry = {"role": msg["role"], "content": msg["content"]}
        if msg.get("emotion"):
            entry["emotion"] = msg["emotion"]
            entry["emotion_intensity"] = msg.get("emotion_intensity", 0.5)
        loaded.append(entry)
    st.session_state.chat_messages = loaded

if "coaching_mode" not in st.session_state:
    st.session_state.coaching_mode = "advise"
if "_last_input" not in st.session_state:
    st.session_state._last_input = ""
if "squad_mode" not in st.session_state:
    st.session_state.squad_mode = None
if "squad_id" not in st.session_state:
    st.session_state.squad_id = None
if "squad_client" not in st.session_state:
    st.session_state.squad_client = SquadClient()
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "session_step" not in st.session_state:
    st.session_state.session_step = 0


# ==================================================
# API KEY SETUP (first-time only)
# ==================================================
from pathlib import Path
env_path = Path(__file__).parent / ".env"

def load_env_vars():
    """Read current .env values."""
    vals = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                vals[key.strip()] = val.strip()
    return vals

def save_env_var(key: str, value: str):
    """Write/update a key in .env."""
    vals = load_env_vars()
    vals[key] = value
    lines = [f"{k}={v}" for k, v in vals.items()]
    env_path.write_text("\n".join(lines) + "\n")

if not orch.llm.is_available:
    st.markdown("""
    <div style="max-width:500px;margin:60px auto;text-align:center;">
        <p style="color:#fff;font-size:1.3rem;font-weight:300;margin-bottom:4px;">AI Coach Companion</p>
        <p style="color:#555;font-size:0.85rem;margin-bottom:32px;">Set up your LLM to get started. Your key stays on your machine.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;">Choose your provider</p>', unsafe_allow_html=True)

    provider_choice = st.radio(
        "LLM Provider",
        ["DeepSeek (recommended -- cheap & fast)", "Google Gemini"],
        label_visibility="collapsed",
    )

    if "DeepSeek" in provider_choice:
        st.markdown('<p style="color:#666;font-size:0.8rem;">Get your key from <a href="https://platform.deepseek.com/api_keys" style="color:#888;">platform.deepseek.com</a></p>', unsafe_allow_html=True)
        api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...", key="setup_ds_key")
        if st.button("Save & Start", key="save_ds"):
            if api_key.strip():
                save_env_var("DEEPSEEK_API_KEY", api_key.strip())
                save_env_var("LLM_PROVIDER", "deepseek")
                st.success("Saved. Restarting app...")
                import time as _t
                _t.sleep(1)
                st.rerun()
            else:
                st.warning("Please paste your API key.")
    else:
        st.markdown('<p style="color:#666;font-size:0.8rem;">Get your key from <a href="https://aistudio.google.com/apikey" style="color:#888;">aistudio.google.com</a></p>', unsafe_allow_html=True)
        api_key = st.text_input("Gemini API Key", type="password", placeholder="AI...", key="setup_gm_key")
        if st.button("Save & Start", key="save_gm"):
            if api_key.strip():
                save_env_var("GEMINI_API_KEY", api_key.strip())
                save_env_var("LLM_PROVIDER", "gemini")
                st.success("Saved. Restarting app...")
                import time as _t
                _t.sleep(1)
                st.rerun()
            else:
                st.warning("Please paste your API key.")

    st.markdown("""
    <div style="text-align:center;margin-top:40px;">
        <p style="color:#333;font-size:0.7rem;">Your API key is stored locally in .env -- never sent anywhere except the LLM provider.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ==================================================
# ONBOARDING FLOW
# ==================================================
if not orch.is_onboarded():
    st.markdown('<p class="onboard-header">Welcome to your AI Coach</p>', unsafe_allow_html=True)
    st.markdown('<p class="onboard-sub">Let\'s set things up. This takes 30 seconds.</p>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("Your name", placeholder="e.g. Amey", key="onboard_name")
    with col2:
        coach_name = st.text_input("Coach name", value="Coach", placeholder="e.g. Kai, Atlas", key="onboard_coach")

    st.markdown('<p class="onboard-label">Coaching tone</p>', unsafe_allow_html=True)
    tone_options = list(TONE_INSTRUCTIONS.keys())
    tone_descriptions = {
        "warm": "Warm -- Supportive, encouraging, safe space",
        "direct": "Direct -- Honest, no fluff, actionable",
        "tough-love": "Tough Love -- Pushes you, calls out excuses",
        "funny": "Funny -- Uses humor, keeps it light",
    }
    selected_tone = st.radio(
        "Select tone",
        tone_options,
        format_func=lambda x: tone_descriptions.get(x, x),
        label_visibility="collapsed",
    )

    st.markdown('<p class="onboard-label">What do you want coaching on?</p>', unsafe_allow_html=True)
    areas = []
    area_cols = st.columns(4)
    area_options = ["Career", "Mental Health", "Relationships", "Fitness",
                    "Productivity", "Self-Growth", "Studies", "Creativity"]
    for i, area in enumerate(area_options):
        with area_cols[i % 4]:
            if st.checkbox(area, key=f"area_{area}"):
                areas.append(area)

    st.markdown("---")

    if st.button("Start Coaching", key="start_coaching"):
        if user_name.strip():
            orch.setup_profile(
                name=user_name.strip(),
                tone=selected_tone,
                coaching_areas=areas,
                coach_name=coach_name.strip() or "Coach",
            )
            st.rerun()
        else:
            st.warning("Please enter your name to continue.")

    st.stop()


# ==================================================
# MAIN APP (Post-Onboarding)
# ==================================================
profile = orch.get_user_profile()
user_name = profile.get("name", "User") if profile else "User"
coach_name = profile.get("coach_name", "Coach") if profile else "Coach"

# Auto-start notification scheduler + streak nudge
if "notif_started" not in st.session_state:
    orch.start_notifications()
    st.session_state.notif_started = True

    streak = orch.get_streak()
    if streak >= 2:
        orch.notifier.send_streak_reminder(streak)
    st.session_state.show_streak_nudge = streak >= 2 and streak > 0


# -- Sidebar: Settings --
with st.sidebar:
    st.markdown("### Settings")

    st.markdown('<p style="color:#666;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;">Notifications</p>', unsafe_allow_html=True)
    reminder_time = st.time_input(
        "Daily reminder time",
        value=datetime.strptime(orch.get_reminder_time(), "%H:%M").time(),
        key="reminder_time",
    )
    if reminder_time:
        orch.set_reminder_time(reminder_time.strftime("%H:%M"))

    nudge_hours = st.slider(
        "Motivational nudge every (hours)",
        min_value=1, max_value=6, value=orch.notifier.get_nudge_interval(),
        key="nudge_interval",
    )
    orch.notifier.set_nudge_interval(nudge_hours)

    notif_col1, notif_col2 = st.columns(2)
    with notif_col1:
        if st.button("Test Reminder", key="test_notif"):
            orch.send_test_notification()
    with notif_col2:
        if st.button("Test Nudge", key="test_nudge"):
            orch.notifier.send_motivational_nudge()

    st.markdown("---")

    st.markdown('<p style="color:#666;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;">Email Digest</p>', unsafe_allow_html=True)
    if orch.is_email_configured():
        digest_time = st.time_input(
            "Daily email time",
            value=datetime.strptime(orch.get_digest_time(), "%H:%M").time(),
            key="digest_time",
        )
        if digest_time:
            orch.set_digest_time(digest_time.strftime("%H:%M"))

        if "email_started" not in st.session_state:
            orch.start_email_scheduler()
            st.session_state.email_started = True

        if st.button("Send Test Email", key="test_email"):
            success = orch.send_test_email()
            if success:
                st.markdown('<p style="color:#555;font-size:0.8rem;">Email sent. Check your inbox.</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#555;font-size:0.8rem;">Failed to send. Check SMTP settings in .env</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#444;font-size:0.8rem;">Add SMTP_EMAIL, SMTP_PASSWORD, and USER_EMAIL to .env to enable email digests.</p>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f'<p style="color:#444;font-size:0.75rem;">Provider: {orch.llm.active_provider}</p>', unsafe_allow_html=True)

    with st.expander("Change API Key"):
        new_key = st.text_input("New API key", type="password", key="change_api_key")
        new_provider = st.radio("Provider", ["deepseek", "gemini"], key="change_provider",
                                index=0 if orch.llm.active_provider == "DeepSeek" else 1)
        if st.button("Update Key", key="update_key"):
            if new_key.strip():
                if new_provider == "deepseek":
                    save_env_var("DEEPSEEK_API_KEY", new_key.strip())
                    save_env_var("LLM_PROVIDER", "deepseek")
                else:
                    save_env_var("GEMINI_API_KEY", new_key.strip())
                    save_env_var("LLM_PROVIDER", "gemini")
                st.success("Updated. Restart app to apply.")


# ==================================================
# LOGIC & SETUP
# ==================================================

def _send_chat_message(user_text: str):
    """Process a user message through the full pipeline."""
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_text,
    })

    result = orch.process_message(user_text, st.session_state.coaching_mode)

    st.session_state.chat_messages[-1]["emotion"] = result["emotion"].get("label", "")
    st.session_state.chat_messages[-1]["emotion_intensity"] = result["emotion"].get("intensity", 0.5)

    st.session_state.chat_messages.append({
        "role": "coach",
        "content": result["response"],
    })

    try:
        st.session_state.current_replies = orch.get_quick_replies(
            result["response"], user_text, result["emotion"].get("label", "")
        )
    except Exception:
        st.session_state.current_replies = ["Got it", "Not sure"]

    st.session_state.session_step += 1

    goal_update = result.get("goal_update", {})
    if goal_update.get("detected"):
        st.session_state._pending_goal_update = goal_update

    return result

# -- Proactive Greeting (first load only) --
if "greeted" not in st.session_state:
    st.session_state.greeted = False

if not st.session_state.greeted and len(st.session_state.chat_messages) == 0:
    try:
        greeting_data = orch.get_greeting()
        greeting_text = greeting_data.get("greeting", f"Hey {user_name}. New session, let's make it count.")
        quick_replies = greeting_data.get("quick_replies", ["Got it", "Not feeling it"])

        st.session_state.chat_messages.append({
            "role": "coach",
            "content": greeting_text,
        })
        st.session_state.current_replies = quick_replies[:2]
        st.session_state.greeted = True
        st.session_state.chat_open = True
    except Exception:
        st.session_state.chat_messages.append({
            "role": "coach",
            "content": f"Hey {user_name}. Let's get to work.",
        })
        st.session_state.current_replies = ["Ready", "Not today"]
        st.session_state.greeted = True
        st.session_state.chat_open = True

# -- Proactive Nudge --
if "nudge_shown" not in st.session_state:
    st.session_state.nudge_shown = False
if "pending_nudge" not in st.session_state:
    st.session_state.pending_nudge = None

if not st.session_state.nudge_shown and len(st.session_state.chat_messages) > 0:
    try:
        nudge = orch.get_proactive_nudge()
        if nudge and nudge.get("message"):
            st.session_state.pending_nudge = nudge
    except Exception:
        pass
    st.session_state.nudge_shown = True

# Initialize quick replies
if "current_replies" not in st.session_state:
    st.session_state.current_replies = []


# ==================================================
# MAIN TABS LAYOUT
# ==================================================

st.markdown(f'<p class="app-title">AI Coach</p>', unsafe_allow_html=True)
st.markdown(f'<p class="app-subtitle">Personal coaching for {user_name} -- powered by memory</p>', unsafe_allow_html=True)

# Show streak nudge banner
if st.session_state.get("show_streak_nudge"):
    streak = orch.get_streak()
    if streak >= 2:
        st.markdown(f"""
        <div style="background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:12px 18px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
            <div>
                <p style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;margin:0;">Streak Alert</p>
                <p style="color:#fff;font-size:0.95rem;margin:4px 0 0 0;">You're on a {streak}-day streak. Don't break it -- check in today.</p>
            </div>
            <p style="color:#fff;font-size:2rem;font-weight:300;margin:0;">{streak}</p>
        </div>
        """, unsafe_allow_html=True)


tab_coach, tab_checkin, tab_progress, tab_world, tab_squad = st.tabs([
    "Coach Session", "Daily Check-in", "Progress", "Your World", "Squad"
])

# == TAB: COACH SESSION ==
with tab_coach:
    st.markdown("<br>", unsafe_allow_html=True)
    # Give it nice margins using columns
    c_left, c_chat, c_right = st.columns([1, 4, 1], gap="large")
    
    with c_chat:
        st.markdown(f"""
        <div style="border-bottom: 1px solid #1a1a1a; padding-bottom: 12px; margin-bottom: 16px;">
            <span style="font-family: 'Inter', sans-serif; font-size: 1.3rem; color: #fff; font-weight: 500;">{coach_name}</span>
            <span style="font-size:0.8rem; color:#555; margin-left:8px; font-weight:300; text-transform:uppercase; letter-spacing:0.05em;">AI Companion</span>
        </div>
        """, unsafe_allow_html=True)

        # Nudges
        nudge = st.session_state.pending_nudge
        if nudge:
            st.markdown(f"""
            <div class="coach-insight" style="margin-bottom: 16px;">
                <p class="coach-insight-type">{nudge.get('type', 'nudge')}</p>
                <p class="coach-insight-text">{nudge['message']}</p>
            </div>
            """, unsafe_allow_html=True)
            nudge_replies = nudge.get("quick_replies", [])
            if nudge_replies:
                nudge_cols = st.columns(len(nudge_replies))
                for i, reply in enumerate(nudge_replies):
                    with nudge_cols[i]:
                        if st.button(reply, key=f"nudge_{i}", use_container_width=True):
                            st.session_state._last_input = ""
                            _send_chat_message(reply)
                            st.session_state.pending_nudge = None
                            st.rerun()

        # Goal updates
        if st.session_state.get("_pending_goal_update"):
            gu = st.session_state._pending_goal_update
            st.markdown(f"""
            <div style="background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
                <p style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px 0;">Goal Progress Detect</p>
                <p style="color:#fff;font-size:0.95rem;margin:0 0 4px 0;">{gu.get("goal_title", "")}: {gu.get("current_progress", 0)}% → {gu.get("suggested_progress", 0)}%</p>
                <p style="color:#555;font-size:0.8rem;margin:0 0 12px 0;">{gu.get("reason", "")}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Update to {gu.get('suggested_progress', 0)}%", key=f"goal_up_{gu.get('goal_id')}", use_container_width=True):
                orch.goal_detector_apply(gu.get("goal_id"), gu.get("suggested_progress", 0))
                st.session_state._pending_goal_update = None
                st.rerun()

        # Chat history container
        chat_container = st.container(height=500, border=False)
        with chat_container:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="panel-msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="panel-msg-coach">{msg["content"]}</div>', unsafe_allow_html=True)
            
            # Session agenda delivery
            if st.session_state.session_step >= 3 and "session_closed" not in st.session_state:
                try:
                    agenda_data = orch.proactive.get_session_agenda()
                    if agenda_data and "closing" in agenda_data:
                        closing = agenda_data.get("closing", "")
                        if closing:
                            st.markdown(f"""
                            <div class="session-summary">
                                <p class="session-summary-title">today's game plan</p>
                                <p class="session-summary-item">{closing}</p>
                            </div>
                            """, unsafe_allow_html=True)
                except Exception:
                    pass

        st.markdown("<br>", unsafe_allow_html=True)

        # Quick Replies
        replies = st.session_state.current_replies
        if replies:
            reply_cols = st.columns(len(replies))
            for i, reply in enumerate(replies):
                with reply_cols[i]:
                    if st.button(reply, key=f"qr_{i}_{len(st.session_state.chat_messages)}", use_container_width=True):
                        _send_chat_message(reply)
                        st.rerun()

        # Input
        user_input = st.chat_input("Say something...")
        if user_input and user_input != st.session_state._last_input:
            st.session_state._last_input = user_input
            _send_chat_message(user_input)
            st.rerun()


# == TAB: DAILY CHECK-IN ==
with tab_checkin:
    streak = orch.get_streak()
    
    # Grid layout for Check-in header
    top_c1, top_c2 = st.columns([1, 2], gap="large")
    with top_c1:
        st.markdown(f"""
        <div class="checkin-card">
            <p class="streak-label">Current Streak</p>
            <p class="streak-number">{streak}</p>
            <p class="streak-label">days</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        mood_score = st.slider(
            "How are you feeling?",
            min_value=1,
            max_value=10,
            value=5,
            key="checkin_mood"
        )

        mood_map = {
            1: "terrible", 2: "bad", 3: "down", 4: "meh",
            5: "neutral", 6: "okay", 7: "good", 8: "great",
            9: "amazing", 10: "incredible"
        }
        mood_label = mood_map.get(mood_score, "neutral")
        st.markdown(f"""
        <div class="metric-card" style="padding:10px;">
            <p class="metric-value" style="font-size:1.6rem;">{mood_score}</p>
            <p class="metric-label">{mood_label}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with top_c2:
        checkin_note = st.text_area(
            "What's on your mind?",
            placeholder="Anything you want to note about today...",
            key="checkin_note",
            height=150,
        )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    st.markdown("### Goal Progress")
    active_goals = orch.get_active_goals()
    goals_updated = []

    if active_goals:
        for goal in active_goals:
            # Tighter columns for goals
            goal_col1, goal_col2 = st.columns([5, 2], gap="medium")
            with goal_col1:
                st.markdown(f"""
                <div class="goal-card" style="padding: 12px 14px; margin-bottom:0;">
                    <p class="goal-title" style="font-size: 0.9rem;">{goal['title']}</p>
                    <div class="progress-bar-bg" style="margin: 6px 0;">
                        <div class="progress-bar-fill" style="width: {goal['progress']}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with goal_col2:
                new_progress = st.number_input(
                    "Progress %",
                    min_value=0, max_value=100,
                    value=goal["progress"],
                    key=f"goal_prog_{goal['id']}"
                )
                if new_progress != goal["progress"]:
                    goals_updated.append({"id": goal["id"], "progress": new_progress})
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <p style="color:#555;margin:0;font-weight:300;">No goals set yet. Add one below.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Add a Goal")
    # Fix gap and alignment for Add Goal
    g_col1, g_col2, g_col3 = st.columns([3, 2, 2], gap="medium")
    with g_col1:
        new_goal_title = st.text_input("Goal", placeholder="e.g. Get placed at a top company", key="new_goal_title", label_visibility="collapsed")
    with g_col2:
        new_goal_cat = st.selectbox("Category", ["career", "health", "personal", "studies", "fitness", "general"], key="new_goal_cat", label_visibility="collapsed")
    with g_col3:
        if st.button("Add Goal", key="add_goal_btn", use_container_width=True):
            if new_goal_title.strip():
                orch.add_goal(new_goal_title.strip(), category=new_goal_cat)
                st.rerun()

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    
    # smaller button for submit checkin
    sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1])
    with sub_c2:
        if st.button("Submit Daily Check-in", type="primary", use_container_width=True, key="submit_checkin"):
            for gu in goals_updated:
                orch.update_goal(gu["id"], progress=gu["progress"])
                if gu["progress"] >= 100:
                    orch.update_goal(gu["id"], status="completed",
                                    completed_at=datetime.now().isoformat())

            orch.add_checkin(mood_score, mood_label, checkin_note,
                            [g["id"] for g in goals_updated])

            st.success("Check-in recorded successfully.")


# == TAB: PROGRESS DASHBOARD ==
with tab_progress:
    stats = orch.get_memory_stats()

    # Top metrics
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['total_messages']}</p>
            <p class="metric-label">Messages</p>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['stored_facts']}</p>
            <p class="metric-label">Known Facts</p>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['episodic_memories']}</p>
            <p class="metric-label">Memories</p>
        </div>
        """, unsafe_allow_html=True)
    with m_col4:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{orch.get_streak()}</p>
            <p class="metric-label">Day Streak</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Token usage section
    token_usage = orch.llm.get_usage()
    st.markdown("### Token Usage (This Session)")
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{token_usage['prompt_tokens']:,}</p>
            <p class="metric-label">Prompt Tokens</p>
        </div>
        """, unsafe_allow_html=True)
    with t_col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{token_usage['completion_tokens']:,}</p>
            <p class="metric-label">Completion Tokens</p>
        </div>
        """, unsafe_allow_html=True)
    with t_col3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{token_usage['total_tokens']:,}</p>
            <p class="metric-label">Total Tokens</p>
        </div>
        """, unsafe_allow_html=True)
    with t_col4:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{token_usage['total_requests']}</p>
            <p class="metric-label">API Requests</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    p_col1, p_col2 = st.columns([2, 1], gap="large")
    with p_col1:
        st.markdown("### Emotional Trajectory")
        mood_data = orch.get_mood_trend(30)
        if mood_data:
            df = pd.DataFrame(mood_data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            emotion_values = {
                "joy": 9, "excitement": 9, "pride": 8, "love": 8, "gratitude": 8,
                "hope": 7, "determination": 7, "relief": 7,
                "calm": 6, "curious": 6, "neutral": 5,
                "stress": 4, "frustration": 3, "anxiety": 3,
                "hurt": 2, "anger": 2, "sadness": 2, "loneliness": 2,
                "self_doubt": 1, "fear": 1,
            }
            df["value"] = df["label"].map(lambda x: emotion_values.get(x, 5))

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["timestamp"],
                y=df["value"],
                mode="lines+markers",
                line=dict(color="#ffffff", width=1.5),
                marker=dict(size=6, color="#ffffff"),
                text=df["label"],
                hovertemplate="%{text}<br>%{x}<extra></extra>",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#888888", size=11),
                xaxis=dict(showgrid=False, color="#444444"),
                yaxis=dict(
                    showgrid=True, gridcolor="#1a1a1a",
                    tickvals=[1, 3, 5, 7, 9],
                    ticktext=["Low", "Stressed", "Neutral", "Good", "Great"],
                    range=[0, 10],
                ),
                margin=dict(l=0, r=0, t=10, b=10),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No mood data yet. Start chatting or check in daily.")

    with p_col2:
        st.markdown("### Emotion Breakdown")
        emotion_summary = orch.get_emotion_summary(30)
        if emotion_summary["count"] > 0:
            breakdown = emotion_summary["breakdown"]
            sorted_emotions = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
            labels = [x[0] for x in sorted_emotions]
            values = [x[1] for x in sorted_emotions]

            fig2 = go.Figure(go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker=dict(
                    color=values,
                    colorscale=[[0, "#1a1a1a"], [1, "#ffffff"]],
                ),
                text=values,
                textposition="outside",
                textfont=dict(color="#888888", size=11),
            ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#888888", size=11),
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, autorange="reversed"),
                margin=dict(l=0, r=40, t=10, b=10),
                height=max(200, len(labels) * 28),
            )
            st.plotly_chart(fig2, use_container_width=True)


# == TAB: YOUR WORLD ==
with tab_world:
    w_col1, w_col2 = st.columns([2, 1], gap="large")
    
    with w_col1:
        st.markdown("### People and Entities")
        st.markdown('<p style="color:#666;font-size:0.85rem;font-weight:300;">Everyone and everything your coach knows about.</p>', unsafe_allow_html=True)
        entities = orch.get_all_entities()

        if entities:
            for entity in entities:
                facts_html = ""
                if entity["facts"]:
                    facts_list = "".join(f"<li>{f}</li>" for f in entity["facts"][:5])
                    facts_html = f'<ul style="color:#777;font-size:0.8rem;margin:6px 0 0 0;padding-left:18px;">{facts_list}</ul>'

                st.markdown(f"""
                <div class="entity-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div>
                            <p class="entity-name">{entity['name']}</p>
                            <p class="entity-type">{entity['type']}</p>
                        </div>
                        <span style="color:#444;font-size:0.75rem;">{entity['mentions']}x mentioned</span>
                    </div>
                    <p class="entity-detail">{entity.get('relationship', '') or 'Relationship not yet known'}</p>
                    {facts_html}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No entities tracked yet. Mention people or places in your chats.")

    with w_col2:
        st.markdown("### Your Profile")
        if profile:
            areas = profile.get("coaching_areas", [])
            areas_text = ", ".join(areas) if areas else "Not set"
            st.markdown(f"""
            <div class="metric-card" style="text-align:left;">
                <p style="color:#ffffff;font-size:1rem;margin:0;font-weight:400;">{profile.get('name', 'User')}</p>
                <p style="color:#666;font-size:0.8rem;margin:4px 0;">Tone: {profile.get('preferred_tone', 'warm')}</p>
                <p style="color:#666;font-size:0.8rem;margin:0;">Focus: {areas_text}</p>
            </div>
            """, unsafe_allow_html=True)

# == TAB: SQUAD ==
with tab_squad:
    st.markdown('<p style="color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;">Squad Goals</p>', unsafe_allow_html=True)
    
    if st.session_state.squad_mode is None:
        setup_col1, setup_col2 = st.columns(2)
        with setup_col1:
            st.markdown("#### Create a Squad")
            squad_name = st.text_input("Squad name", placeholder="e.g. Grind Gang", key="sq_name")
            if st.button("Create", key="create_squad"):
                if squad_name:
                    import uuid
                    invite_code = uuid.uuid4().hex[:8].upper()
                    squad_id = orch.db.create_squad(squad_name, invite_code, user_name)
                    orch.db.add_squad_member(squad_id, user_name, is_self=True)
                    start_squad_server(orch.db)
                    st.session_state.squad_mode = "host"
                    st.session_state.squad_id = squad_id
                    st.rerun()

        with setup_col2:
            st.markdown("#### Join a Squad")
            host_url = st.text_input("Host URL", placeholder="http://192.168.1.5:8502", key="sq_host")
            join_code = st.text_input("Invite code", placeholder="e.g. A1B2C3D4", key="sq_code")
            if st.button("Join", key="join_squad"):
                if host_url and join_code:
                    client = st.session_state.squad_client
                    result = client.connect(host_url, join_code, user_name)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.squad_mode = "client"
                        st.session_state.squad_id = result["squad_id"]
                        st.rerun()
    else:
        st.info("Squad Mode is Active. Disconnect requires restart for now.")
