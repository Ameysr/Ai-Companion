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
    st.session_state.chat_messages = []
if "coaching_mode" not in st.session_state:
    st.session_state.coaching_mode = "advise"
if "_last_input" not in st.session_state:
    st.session_state._last_input = ""


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

    if st.button("Start Coaching", use_container_width=True):
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

# Auto-start notification scheduler
if "notif_started" not in st.session_state:
    orch.start_notifications()
    st.session_state.notif_started = True

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

    if st.button("Test Notification", key="test_notif"):
        orch.send_test_notification()
        st.markdown('<p style="color:#555;font-size:0.8rem;">Sent! Check your taskbar.</p>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f'<p style="color:#444;font-size:0.75rem;">Provider: {orch.llm.active_provider}</p>', unsafe_allow_html=True)

# Title
st.markdown(f'<p class="app-title">AI Coach</p>', unsafe_allow_html=True)
st.markdown(f'<p class="app-subtitle">Personal coaching for {user_name} — powered by memory</p>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_chat, tab_checkin, tab_progress, tab_world = st.tabs([
    "Chat", "Daily Check-in", "Progress", "Your World"
])


# ══════════════════════════════════════════════
# TAB 1: CHAT
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

    # Display chat history
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

    # Input
    user_input = st.chat_input(f"Talk to {coach_name}...")

    if user_input and user_input != st.session_state._last_input:
        st.session_state._last_input = user_input

        # Add user message to display
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input,
        })

        # Show user message immediately
        st.markdown(f'<div class="chat-user">{user_input}</div>', unsafe_allow_html=True)

        # Typing indicator
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            '<div class="chat-coach" style="color:#444;font-style:italic;">thinking...</div>',
            unsafe_allow_html=True,
        )

        # Process through orchestrator
        result = orch.process_message(user_input, st.session_state.coaching_mode)

        # Clear typing indicator
        typing_placeholder.empty()

        # Update user message with emotion
        st.session_state.chat_messages[-1]["emotion"] = result["emotion"].get("label", "")
        st.session_state.chat_messages[-1]["emotion_intensity"] = result["emotion"].get("intensity", 0.5)

        # Stream the response word by word
        response_text = result["response"]
        response_placeholder = st.empty()
        streamed = ""
        words = response_text.split(" ")
        for i, word in enumerate(words):
            streamed += word + " "
            response_placeholder.markdown(
                f'<div class="chat-coach">{streamed.strip()}</div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.03)

        # Add coach response to state
        st.session_state.chat_messages.append({
            "role": "coach",
            "content": response_text,
        })

        # Show emotion tag
        emotion_label = result["emotion"].get("label", "")
        if emotion_label:
            intensity = result["emotion"].get("intensity", 0.5)
            tag_class = "emotion-tag-strong" if intensity > 0.6 else "emotion-tag"
            st.markdown(
                f'<span class="{tag_class}">{emotion_label}</span>',
                unsafe_allow_html=True,
            )


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
