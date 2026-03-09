"""
app.py — AI Coach Companion: Main Streamlit Application
4-tab interface: Chat, Daily Check-in, Progress Dashboard, Your World
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

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Coach",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject CSS
st.markdown(MAIN_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Initialize Orchestrator (cached)
# ──────────────────────────────────────────────
@st.cache_resource
def get_orchestrator():
    return Orchestrator()

orch = get_orchestrator()

# ──────────────────────────────────────────────
# Session State
# ──────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    # Load chat history from database so it persists across reloads
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
    st.session_state.squad_mode = None  # None, "host", or "client"
if "squad_id" not in st.session_state:
    st.session_state.squad_id = None
if "squad_client" not in st.session_state:
    st.session_state.squad_client = SquadClient()


# ══════════════════════════════════════════════
# API KEY SETUP (first-time only)
# ══════════════════════════════════════════════
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
        ["DeepSeek (recommended — cheap & fast)", "Google Gemini"],
        label_visibility="collapsed",
    )

    if "DeepSeek" in provider_choice:
        st.markdown('<p style="color:#666;font-size:0.8rem;">Get your key from <a href="https://platform.deepseek.com/api_keys" style="color:#888;">platform.deepseek.com</a></p>', unsafe_allow_html=True)
        api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...", key="setup_ds_key")
        if st.button("Save & Start", key="save_ds"):
            if api_key.strip():
                save_env_var("DEEPSEEK_API_KEY", api_key.strip())
                save_env_var("LLM_PROVIDER", "deepseek")
                st.success("Saved! Restarting app...")
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
                st.success("Saved! Restarting app...")
                import time as _t
                _t.sleep(1)
                st.rerun()
            else:
                st.warning("Please paste your API key.")

    st.markdown("""
    <div style="text-align:center;margin-top:40px;">
        <p style="color:#333;font-size:0.7rem;">Your API key is stored locally in .env — never sent anywhere except the LLM provider.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════
# ONBOARDING FLOW
# ══════════════════════════════════════════════
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
        "warm": "Warm — Supportive, encouraging, safe space",
        "direct": "Direct — Honest, no fluff, actionable",
        "tough-love": "Tough Love — Pushes you, calls out excuses",
        "funny": "Funny — Uses humor, keeps it light",
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


# ══════════════════════════════════════════════
# MAIN APP (Post-Onboarding)
# ══════════════════════════════════════════════
profile = orch.get_user_profile()
user_name = profile.get("name", "User") if profile else "User"
coach_name = profile.get("coach_name", "Coach") if profile else "Coach"

# Auto-start notification scheduler + streak nudge
if "notif_started" not in st.session_state:
    orch.start_notifications()
    st.session_state.notif_started = True

    # Send streak reminder if applicable
    streak = orch.get_streak()
    if streak >= 2:
        orch.notifier.send_streak_reminder(streak)
    st.session_state.show_streak_nudge = streak >= 2 and streak > 0

# Show streak nudge banner
if st.session_state.get("show_streak_nudge"):
    streak = orch.get_streak()
    if streak >= 2:
        st.markdown(f"""
        <div style="background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:12px 18px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
            <div>
                <p style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;margin:0;">Streak Alert</p>
                <p style="color:#fff;font-size:0.95rem;margin:4px 0 0 0;">You're on a {streak}-day streak. Don't break it — check in today!</p>
            </div>
            <p style="color:#fff;font-size:2rem;font-weight:300;margin:0;">{streak}</p>
        </div>
        """, unsafe_allow_html=True)

# ── Sidebar: Settings ────────────────────────
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
                st.markdown('<p style="color:#555;font-size:0.8rem;">Email sent! Check your inbox.</p>', unsafe_allow_html=True)
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
                st.success("Updated! Restart app to apply.")

# Title
st.markdown(f'<p class="app-title">AI Coach</p>', unsafe_allow_html=True)
st.markdown(f'<p class="app-subtitle">Personal coaching for {user_name} — powered by memory</p>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_chat, tab_checkin, tab_progress, tab_world, tab_squad = st.tabs([
    "Chat", "Daily Check-in", "Progress", "Your World", "Squad"
])


# ══════════════════════════════════════════════
# TAB 1: CHAT (Proactive)
# ══════════════════════════════════════════════
with tab_chat:
    # Coaching mode selector
    mode_col1, mode_col2 = st.columns([3, 1])
    with mode_col2:
        mode_labels = {
            "listen": "Listen",
            "advise": "Advise",
            "challenge": "Challenge",
            "celebrate": "Celebrate",
        }
        selected_mode = st.selectbox(
            "Mode",
            COACHING_MODES,
            format_func=lambda x: mode_labels.get(x, x),
            index=COACHING_MODES.index(st.session_state.coaching_mode),
            key="mode_select",
            label_visibility="collapsed",
        )
        st.session_state.coaching_mode = selected_mode

    # ── Proactive Greeting (first load only) ──────
    if "greeted" not in st.session_state:
        st.session_state.greeted = False

    if not st.session_state.greeted and len(st.session_state.chat_messages) == 0:
        try:
            greeting_data = orch.get_greeting()
            greeting_text = greeting_data.get("greeting", f"What's on your mind, {user_name}?")
            quick_replies = greeting_data.get("quick_replies", ["Feeling good", "Need advice", "Just venting"])

            st.session_state.chat_messages.append({
                "role": "coach",
                "content": greeting_text,
            })
            st.session_state.current_replies = quick_replies
            st.session_state.greeted = True
        except Exception:
            st.session_state.chat_messages.append({
                "role": "coach",
                "content": f"What's going on today, {user_name}?",
            })
            st.session_state.current_replies = ["Making progress", "Stuck on something", "Just checking in"]
            st.session_state.greeted = True

    # ── Proactive Nudge Banner ────────────────────
    if "nudge_shown" not in st.session_state:
        st.session_state.nudge_shown = False

    if not st.session_state.nudge_shown and len(st.session_state.chat_messages) > 0:
        try:
            nudge = orch.get_proactive_nudge()
            if nudge and nudge.get("message"):
                st.markdown(f"""
                <div style="background:#111;border-left:3px solid #333;border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:12px;">
                    <p style="color:#888;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 4px 0;">{nudge.get('type', 'nudge')}</p>
                    <p style="color:#ddd;font-size:0.9rem;margin:0;">{nudge['message']}</p>
                </div>
                """, unsafe_allow_html=True)

                nudge_replies = nudge.get("quick_replies", [])
                if nudge_replies:
                    nudge_cols = st.columns(len(nudge_replies))
                    for i, reply in enumerate(nudge_replies):
                        with nudge_cols[i]:
                            if st.button(reply, key=f"nudge_{i}"):
                                st.session_state._last_input = ""
                                st.session_state.chat_messages.append({"role": "user", "content": reply})
                                result = orch.process_message(reply, st.session_state.coaching_mode)
                                st.session_state.chat_messages.append({"role": "coach", "content": result["response"]})
                                try:
                                    st.session_state.current_replies = orch.get_quick_replies(
                                        result["response"], reply, result["emotion"].get("label", "")
                                    )
                                except Exception:
                                    st.session_state.current_replies = ["Got it", "Tell me more", "What else?"]
                                st.session_state.nudge_shown = True
                                st.rerun()
        except Exception:
            pass
        st.session_state.nudge_shown = True

    # ── Display Chat History ──────────────────────
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("emotion"):
                intensity = msg.get("emotion_intensity", 0.5)
                tag_class = "emotion-tag-strong" if intensity > 0.6 else "emotion-tag"
                st.markdown(
                    f'<span class="{tag_class}">{msg["emotion"]}</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(f'<div class="chat-coach">{msg["content"]}</div>', unsafe_allow_html=True)

    # ── Quick Reply Buttons ───────────────────────
    if "current_replies" not in st.session_state:
        st.session_state.current_replies = []

    replies = st.session_state.current_replies
    if replies:
        reply_cols = st.columns(len(replies))
        for i, reply in enumerate(replies):
            with reply_cols[i]:
                if st.button(reply, key=f"qr_{i}_{len(st.session_state.chat_messages)}"):
                    st.session_state.chat_messages.append({"role": "user", "content": reply})

                    result = orch.process_message(reply, st.session_state.coaching_mode)

                    st.session_state.chat_messages[-1]["emotion"] = result["emotion"].get("label", "")
                    st.session_state.chat_messages[-1]["emotion_intensity"] = result["emotion"].get("intensity", 0.5)
                    st.session_state.chat_messages.append({"role": "coach", "content": result["response"]})

                    # Generate next quick replies
                    try:
                        st.session_state.current_replies = orch.get_quick_replies(
                            result["response"], reply, result["emotion"].get("label", "")
                        )
                    except Exception:
                        st.session_state.current_replies = ["Got it", "Tell me more", "What else?"]

                    st.rerun()

    # ── Text Input (still available) ──────────────
    user_input = st.chat_input(f"Or type your own message...")

    if user_input and user_input != st.session_state._last_input:
        st.session_state._last_input = user_input

        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input,
        })

        st.markdown(f'<div class="chat-user">{user_input}</div>', unsafe_allow_html=True)

        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            '<div class="chat-coach" style="color:#444;font-style:italic;">thinking...</div>',
            unsafe_allow_html=True,
        )

        result = orch.process_message(user_input, st.session_state.coaching_mode)
        typing_placeholder.empty()

        st.session_state.chat_messages[-1]["emotion"] = result["emotion"].get("label", "")
        st.session_state.chat_messages[-1]["emotion_intensity"] = result["emotion"].get("intensity", 0.5)

        response_text = result["response"]
        response_placeholder = st.empty()
        streamed = ""
        words = response_text.split(" ")
        for word in words:
            streamed += word + " "
            response_placeholder.markdown(
                f'<div class="chat-coach">{streamed.strip()}</div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.03)

        st.session_state.chat_messages.append({
            "role": "coach",
            "content": response_text,
        })

        # Generate quick replies for next turn
        try:
            emotion_label = result["emotion"].get("label", "")
            st.session_state.current_replies = orch.get_quick_replies(
                response_text, user_input, emotion_label
            )
        except Exception:
            st.session_state.current_replies = ["Got it", "Tell me more", "What else?"]

        # Goal update detection
        goal_update = result.get("goal_update", {})
        if goal_update.get("detected"):
            goal_title = goal_update.get("goal_title", "")
            current = goal_update.get("current_progress", 0)
            suggested = goal_update.get("suggested_progress", 0)
            reason = goal_update.get("reason", "")
            goal_id = goal_update.get("goal_id")

            st.markdown(f"""
            <div style="background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:14px 18px;margin:8px 0;">
                <p style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px 0;">Goal Progress Detected</p>
                <p style="color:#fff;font-size:0.95rem;margin:0;">{goal_title}: {current}% to {suggested}%</p>
                <p style="color:#666;font-size:0.8rem;margin:4px 0 0 0;">{reason}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Update to {suggested}%", key=f"goal_up_{goal_id}"):
                orch.goal_detector_apply(goal_id, suggested)


# ══════════════════════════════════════════════
# TAB 2: DAILY CHECK-IN
# ══════════════════════════════════════════════
with tab_checkin:
    streak = orch.get_streak()

    # Streak display
    st.markdown(f"""
    <div class="checkin-card">
        <p class="streak-label">Current Streak</p>
        <p class="streak-number">{streak}</p>
        <p class="streak-label">days</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### How are you feeling today?")

    mood_col1, mood_col2 = st.columns([1, 2])
    with mood_col1:
        mood_score = st.slider(
            "Mood",
            min_value=1,
            max_value=10,
            value=5,
            key="checkin_mood",
            label_visibility="collapsed",
        )

        mood_map = {
            1: "terrible", 2: "bad", 3: "down", 4: "meh",
            5: "neutral", 6: "okay", 7: "good", 8: "great",
            9: "amazing", 10: "incredible"
        }
        mood_label = mood_map.get(mood_score, "neutral")
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{mood_score}</p>
            <p class="metric-label">{mood_label}</p>
        </div>
        """, unsafe_allow_html=True)

    with mood_col2:
        checkin_note = st.text_area(
            "What's on your mind?",
            placeholder="Anything you want to note about today...",
            key="checkin_note",
            height=120,
        )

    # Goal updates
    st.markdown("### Goal Progress")
    active_goals = orch.get_active_goals()
    goals_updated = []

    if active_goals:
        for goal in active_goals:
            goal_col1, goal_col2 = st.columns([3, 1])
            with goal_col1:
                st.markdown(f"""
                <div class="goal-card">
                    <p class="goal-title">{goal['title']}</p>
                    <p class="goal-progress">{goal['progress']}% complete</p>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: {goal['progress']}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with goal_col2:
                new_progress = st.number_input(
                    "Progress",
                    min_value=0, max_value=100,
                    value=goal["progress"],
                    key=f"goal_prog_{goal['id']}",
                    label_visibility="collapsed",
                )
                if new_progress != goal["progress"]:
                    goals_updated.append({"id": goal["id"], "progress": new_progress})
    else:
        st.markdown("""
        <div class="metric-card">
            <p style="color:#555;margin:0;font-weight:300;">No goals set yet. Add one below.</p>
        </div>
        """, unsafe_allow_html=True)

    # Add new goal
    st.markdown("### Add a Goal")
    goal_col1, goal_col2, goal_col3 = st.columns([2, 1, 1])
    with goal_col1:
        new_goal_title = st.text_input("Goal", placeholder="e.g. Get placed at a top company", key="new_goal_title", label_visibility="collapsed")
    with goal_col2:
        new_goal_cat = st.selectbox("Category", ["career", "health", "personal", "studies", "fitness", "general"], key="new_goal_cat", label_visibility="collapsed")
    with goal_col3:
        if st.button("Add Goal", key="add_goal_btn"):
            if new_goal_title.strip():
                orch.add_goal(new_goal_title.strip(), category=new_goal_cat)
                st.rerun()

    st.markdown("---")

    # Submit check-in
    if st.button("Submit Check-in", use_container_width=True, key="submit_checkin"):
        # Update goals
        for gu in goals_updated:
            orch.update_goal(gu["id"], progress=gu["progress"])
            if gu["progress"] >= 100:
                orch.update_goal(gu["id"], status="completed",
                                completed_at=datetime.now().isoformat())

        # Save check-in
        orch.add_checkin(mood_score, mood_label, checkin_note,
                         [g["id"] for g in goals_updated])

        st.markdown("""
        <div class="metric-card" style="border-color:#333;">
            <p style="color:#ffffff;margin:0;font-weight:400;">Check-in recorded.</p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 3: PROGRESS DASHBOARD
# ══════════════════════════════════════════════
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

    # Mood Graph
    st.markdown("### Emotional Trajectory")
    mood_data = orch.get_mood_trend(30)

    if mood_data:
        df = pd.DataFrame(mood_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Map emotions to numeric values for graphing
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
            plot_bgcolor="#0a0a0a",
            paper_bgcolor="#0a0a0a",
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
        st.markdown("""
        <div class="metric-card">
            <p style="color:#555;margin:0;font-weight:300;">No mood data yet. Start chatting or check in daily.</p>
        </div>
        """, unsafe_allow_html=True)

    # Emotion Breakdown
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
            plot_bgcolor="#0a0a0a",
            paper_bgcolor="#0a0a0a",
            font=dict(color="#888888", size=11),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, autorange="reversed"),
            margin=dict(l=0, r=40, t=10, b=10),
            height=max(200, len(labels) * 28),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Goals Overview
    st.markdown("### Goals")
    all_goals = orch.get_all_goals()
    if all_goals:
        for goal in all_goals:
            status_color = "#ffffff" if goal["status"] == "active" else "#555555"
            st.markdown(f"""
            <div class="goal-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <p class="goal-title">{goal['title']}</p>
                    <span style="color:{status_color};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">{goal['status']}</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {goal['progress']}%"></div>
                </div>
                <p class="goal-progress">{goal['progress']}% — {goal.get('category', 'general')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <p style="color:#555;margin:0;font-weight:300;">No goals yet. Set some in the Daily Check-in tab.</p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 4: YOUR WORLD
# ══════════════════════════════════════════════
with tab_world:
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
                <p style="color:#333;font-size:0.7rem;margin:8px 0 0 0;">First: {entity['first_seen']} — Last: {entity['last_seen']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <p style="color:#555;margin:0;font-weight:300;">No entities tracked yet. Mention people or places in your chats.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # User Profile Summary
    st.markdown("### Your Profile")
    if profile:
        areas = profile.get("coaching_areas", [])
        areas_text = ", ".join(areas) if areas else "Not set"
        st.markdown(f"""
        <div class="metric-card" style="text-align:left;">
            <p style="color:#ffffff;font-size:1rem;margin:0;font-weight:400;">{profile.get('name', 'User')}</p>
            <p style="color:#666;font-size:0.8rem;margin:4px 0;">Tone: {profile.get('preferred_tone', 'warm')} — Coach: {profile.get('coach_name', 'Coach')}</p>
            <p style="color:#666;font-size:0.8rem;margin:0;">Focus: {areas_text}</p>
            <p style="color:#333;font-size:0.7rem;margin:8px 0 0 0;">Member since {profile.get('created_at', 'unknown')}</p>
        </div>
        """, unsafe_allow_html=True)

    # Memory Stats
    st.markdown("### Memory Stats")
    stats = orch.get_memory_stats()
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['episodic_memories']}</p>
            <p class="metric-label">Episodes</p>
        </div>
        """, unsafe_allow_html=True)
    with stat_col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['stored_facts']}</p>
            <p class="metric-label">Facts</p>
        </div>
        """, unsafe_allow_html=True)
    with stat_col3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['narrative_threads']}</p>
            <p class="metric-label">Narratives</p>
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;padding:16px 0;">
    <p style="color:#2a2a2a;font-size:0.75rem;letter-spacing:0.05em;">
        AI Coach Companion — Local-first, memory-powered personal coaching
    </p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 5: SQUAD
# ══════════════════════════════════════════════
with tab_squad:
    st.markdown('<p style="color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;">Squad Goals</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#555;font-size:0.85rem;">Shared goals with your friends. Your private chat and emotions are never shared.</p>', unsafe_allow_html=True)

    # ── Setup: Create or Join ──────────────────
    if st.session_state.squad_mode is None:
        st.markdown("---")
        setup_col1, setup_col2 = st.columns(2)

        with setup_col1:
            st.markdown('<p style="color:#999;font-size:0.85rem;font-weight:500;">Create a Squad</p>', unsafe_allow_html=True)
            squad_name = st.text_input("Squad name", placeholder="e.g. Grind Gang", key="sq_name")
            if st.button("Create Squad", key="create_squad"):
                if squad_name:
                    import uuid
                    invite_code = uuid.uuid4().hex[:8].upper()
                    squad_id = orch.db.create_squad(squad_name, invite_code, user_name)
                    orch.db.add_squad_member(squad_id, user_name, is_self=True)

                    # Start the sync server
                    port = start_squad_server(orch.db)

                    st.session_state.squad_mode = "host"
                    st.session_state.squad_id = squad_id
                    st.session_state.invite_code = invite_code
                    st.rerun()

        with setup_col2:
            st.markdown('<p style="color:#999;font-size:0.85rem;font-weight:500;">Join a Squad</p>', unsafe_allow_html=True)
            host_url = st.text_input("Host URL", placeholder="http://192.168.1.5:8502", key="sq_host")
            join_code = st.text_input("Invite code", placeholder="e.g. A1B2C3D4", key="sq_code")
            if st.button("Join Squad", key="join_squad"):
                if host_url and join_code:
                    client = st.session_state.squad_client
                    result = client.connect(host_url, join_code, user_name)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.squad_mode = "client"
                        st.session_state.squad_id = result["squad_id"]
                        st.rerun()

    # ── Host View ─────────────────────────────────
    elif st.session_state.squad_mode == "host":
        squad_id = st.session_state.squad_id
        squad = orch.db.get_squad(squad_id=squad_id)

        if not squad_running():
            start_squad_server(orch.db)

        # Squad header
        import socket
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "127.0.0.1"

        st.markdown(f"""
        <div style="background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:16px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <p style="color:#fff;font-size:1.1rem;font-weight:400;margin:0;">{squad['name']}</p>
                    <p style="color:#555;font-size:0.75rem;margin:4px 0 0 0;">You are the host</p>
                </div>
                <div style="text-align:right;">
                    <p style="color:#888;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;margin:0;">Invite Code</p>
                    <p style="color:#fff;font-size:1.2rem;font-weight:300;letter-spacing:0.15em;margin:0;">{squad['invite_code']}</p>
                    <p style="color:#444;font-size:0.7rem;margin:4px 0 0 0;">http://{local_ip}:8502</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Members
        members = orch.db.get_squad_members(squad_id)
        member_names = [m["member_name"] for m in members]
        st.markdown(f'<p style="color:#666;font-size:0.75rem;">Members: {" / ".join(member_names)}</p>', unsafe_allow_html=True)

        st.markdown("---")

        # Add goal
        goal_col1, goal_col2 = st.columns([3, 1])
        with goal_col1:
            new_goal = st.text_input("Add shared goal", placeholder="e.g. DSA daily for 30 days", key="sq_goal_input", label_visibility="collapsed")
        with goal_col2:
            if st.button("Add Goal", key="sq_add_goal"):
                if new_goal:
                    orch.db.add_squad_goal(squad_id, new_goal)
                    st.rerun()

        # Goals + progress
        goals = orch.db.get_squad_goals(squad_id)
        leaderboard = orch.db.get_squad_leaderboard(squad_id)

        for goal in goals:
            st.markdown(f"""
            <div style="background:#0f0f0f;border:1px solid #1a1a1a;border-radius:6px;padding:12px 16px;margin-bottom:8px;">
                <p style="color:#fff;font-size:0.9rem;margin:0 0 8px 0;">{goal['title']}</p>
            </div>
            """, unsafe_allow_html=True)

            # Show each member's progress for this goal
            goal_entries = [e for e in leaderboard if e["goal_id"] == goal["id"]]
            for entry in goal_entries:
                bar_color = "#fff" if entry["member_name"] == user_name else "#555"
                is_me = " (you)" if entry["member_name"] == user_name else ""
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:4px 16px;">
                    <p style="color:#888;font-size:0.8rem;width:100px;margin:0;">{entry['member_name']}{is_me}</p>
                    <div style="flex:1;background:#1a1a1a;border-radius:3px;height:4px;overflow:hidden;">
                        <div style="background:{bar_color};height:100%;width:{max(entry['progress'], 1)}%;border-radius:3px;"></div>
                    </div>
                    <p style="color:#666;font-size:0.75rem;width:40px;text-align:right;margin:0;">{entry['progress']}%</p>
                </div>
                """, unsafe_allow_html=True)

            # Update my progress
            my_member = next((m for m in members if m["is_self"]), None)
            if my_member:
                my_entry = next((e for e in goal_entries if e["member_id"] == my_member["id"]), None)
                current_prog = my_entry["progress"] if my_entry else 0
                new_prog = st.number_input(
                    f"Your progress", min_value=0, max_value=100,
                    value=current_prog, key=f"sq_prog_{goal['id']}",
                    label_visibility="collapsed",
                )
                if new_prog != current_prog:
                    orch.db.update_squad_goal_progress(goal["id"], my_member["id"], new_prog)

        # Leaderboard summary
        if goals:
            st.markdown("---")
            st.markdown('<p style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;">Leaderboard</p>', unsafe_allow_html=True)
            summary = orch.db.get_squad_summary(squad_id)
            for i, rank in enumerate(summary["rankings"]):
                medal = "" if i > 0 else "#1"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #111;">
                    <p style="color:#fff;font-size:0.9rem;margin:0;">{medal} {rank['name']}</p>
                    <p style="color:#888;font-size:0.9rem;margin:0;">{rank['avg_progress']}% avg</p>
                </div>
                """, unsafe_allow_html=True)

    # ── Client View ───────────────────────────────
    elif st.session_state.squad_mode == "client":
        client = st.session_state.squad_client

        # Fetch data from host
        leaderboard_data = client.get_leaderboard()
        goals = client.get_goals()
        motivation = client.get_motivation()

        # Motivation banner
        if motivation.get("message"):
            st.markdown(f"""
            <div style="background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:14px 18px;margin-bottom:16px;">
                <p style="color:#fff;font-size:0.95rem;margin:0;">{motivation['message']}</p>
            </div>
            """, unsafe_allow_html=True)

        # Goals + update progress
        for goal in goals:
            st.markdown(f"""
            <div style="background:#0f0f0f;border:1px solid #1a1a1a;border-radius:6px;padding:12px 16px;margin-bottom:8px;">
                <p style="color:#fff;font-size:0.9rem;margin:0;">{goal['title']}</p>
            </div>
            """, unsafe_allow_html=True)

            # Show leaderboard entries for this goal
            goal_entries = [e for e in leaderboard_data.get("leaderboard", []) if e["goal_id"] == goal["id"]]
            for entry in goal_entries:
                is_me = " (you)" if entry["member_name"].lower() == user_name.lower() else ""
                bar_color = "#fff" if is_me else "#555"
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:4px 16px;">
                    <p style="color:#888;font-size:0.8rem;width:100px;margin:0;">{entry['member_name']}{is_me}</p>
                    <div style="flex:1;background:#1a1a1a;border-radius:3px;height:4px;overflow:hidden;">
                        <div style="background:{bar_color};height:100%;width:{max(entry['progress'], 1)}%;border-radius:3px;"></div>
                    </div>
                    <p style="color:#666;font-size:0.75rem;width:40px;text-align:right;margin:0;">{entry['progress']}%</p>
                </div>
                """, unsafe_allow_html=True)

            new_prog = st.number_input(
                f"Your progress", min_value=0, max_value=100,
                value=0, key=f"sq_client_prog_{goal['id']}",
                label_visibility="collapsed",
            )
            if st.button("Update", key=f"sq_client_update_{goal['id']}"):
                client.update_progress(goal["id"], new_prog)
                st.rerun()

        # Add goal (anyone can)
        st.markdown("---")
        new_goal_client = st.text_input("Add shared goal", placeholder="e.g. Read 1 chapter daily", key="sq_client_goal")
        if st.button("Add Goal", key="sq_client_add"):
            if new_goal_client:
                client.create_goal(new_goal_client)
                st.rerun()

        # Leaderboard
        rankings = leaderboard_data.get("rankings", [])
        if rankings:
            st.markdown("---")
            st.markdown('<p style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;">Leaderboard</p>', unsafe_allow_html=True)
            for i, rank in enumerate(rankings):
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #111;">
                    <p style="color:#fff;font-size:0.9rem;margin:0;">{'#1' if i == 0 else ''} {rank['name']}</p>
                    <p style="color:#888;font-size:0.9rem;margin:0;">{rank['avg_progress']}% avg</p>
                </div>
                """, unsafe_allow_html=True)

        if st.button("Refresh", key="sq_refresh"):
            st.rerun()
