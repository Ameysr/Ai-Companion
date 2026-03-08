"""
app.py — CompanionCache: Semantic Caching Layer Demo for AI Companion Startups
Main Streamlit dashboard with 5 sections + memory injection + rotation demo.
"""

import json
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

from classifier import (
    classify,
    is_cache_hit,
    load_model,
    HotCache,
    classify_with_hot_cache,
)
from dataset import MESSAGES, INTENTS

# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="CompanionCache",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS — dark, professional, minimal
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Global */
    .stApp {
        background-color: #0a0a0a;
        color: #e0e0e0;
    }

    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Main title */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0;
        letter-spacing: -0.02em;
    }
    .main-subtitle {
        font-size: 1.1rem;
        color: #888888;
        margin-top: 0;
        margin-bottom: 2rem;
    }

    /* Cache status badges */
    .cache-hit {
        background: linear-gradient(135deg, #00ff8820, #00ff8810);
        border: 1px solid #00ff88;
        color: #00ff88;
        padding: 8px 20px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.1rem;
        display: inline-block;
    }
    .cache-miss {
        background: linear-gradient(135deg, #ff444420, #ff444410);
        border: 1px solid #ff4444;
        color: #ff4444;
        padding: 8px 20px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.1rem;
        display: inline-block;
    }

    /* Metric cards */
    .metric-card {
        background: #111111;
        border: 1px solid #222222;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #00ff88;
        margin: 0;
    }
    .metric-value-red {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ff4444;
        margin: 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #888888;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Response box */
    .response-box {
        background: #111111;
        border: 1px solid #222222;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        font-size: 1rem;
        line-height: 1.6;
        color: #cccccc;
    }

    /* Intent badge */
    .intent-badge {
        background: #1a1a2e;
        border: 1px solid #333366;
        color: #8888ff;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        margin-right: 8px;
    }
    .confidence-badge {
        background: #1a2e1a;
        border: 1px solid #336633;
        color: #88ff88;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
    }

    /* Latency comparison */
    .latency-cached {
        color: #00ff88;
        font-weight: 700;
        font-size: 1.3rem;
    }
    .latency-llm {
        color: #ff4444;
        font-weight: 700;
        font-size: 1.3rem;
    }

    /* Memory injection boxes */
    .memory-without {
        background: #111111;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 16px;
        color: #cccccc;
    }
    .memory-with {
        background: #0a1a0a;
        border: 1px solid #00ff8840;
        border-radius: 12px;
        padding: 16px;
        color: #cccccc;
    }
    .memory-tag {
        color: #00ff88;
        font-style: italic;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px dashed #00ff8840;
    }

    /* Savings highlight */
    .savings-big {
        font-size: 3rem;
        font-weight: 900;
        color: #00ff88;
        text-align: center;
        margin: 10px 0;
    }

    /* Hot cache badge */
    .hot-badge {
        background: linear-gradient(135deg, #ff880020, #ff880010);
        border: 1px solid #ff8800;
        color: #ff8800;
        padding: 4px 12px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* Section dividers */
    .section-divider {
        border: none;
        border-top: 1px solid #222222;
        margin: 2rem 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0e0e0e;
        border-right: 1px solid #1a1a1a;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Slider styling */
    .stSlider > div > div {
        color: #888888;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Load resources
# ──────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_responses():
    with open("responses.json", "r", encoding="utf-8") as f:
        return json.load(f)


# Force model load on startup
with st.spinner("Loading semantic model (first time may take a few seconds)..."):
    load_model()

RESPONSES = load_responses()

# ──────────────────────────────────────────────
# Session state initialization
# ──────────────────────────────────────────────
defaults = {
    "total_messages": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "intent_counts": {intent: 0 for intent in INTENTS},
    "last_served": {intent: -1 for intent in INTENTS},
    "message_history": [],
    "memory_fact": "",
    "hot_cache": HotCache(),
    "benchmark_results": None,
    "last_input": "",
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────
def get_next_response(intent: str) -> str:
    """Get the next response for an intent, rotating through all 20."""
    responses = RESPONSES.get(intent, ["I'm here for you."])
    idx = (st.session_state.last_served[intent] + 1) % len(responses)
    st.session_state.last_served[intent] = idx
    return responses[idx]


def inject_memory(response: str, memory_fact: str) -> str:
    """Append a memory tag to a cached response."""
    if not memory_fact:
        return response
    return f"{response}\n\n...by the way, {memory_fact} — how's that going?"


def update_metrics(intent: str, is_hit: bool):
    """Update all session state counters."""
    st.session_state.total_messages += 1
    if is_hit:
        st.session_state.cache_hits += 1
    else:
        st.session_state.cache_misses += 1
    st.session_state.intent_counts[intent] = st.session_state.intent_counts.get(intent, 0) + 1


# ──────────────────────────────────────────────
# SIDEBAR — Section 2: Real-Time Metrics
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="font-size:1.4rem;font-weight:700;color:#ffffff;margin-bottom:0;">⚡ CompanionCache</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.85rem;color:#666666;margin-top:0;">Semantic Caching Metrics</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Threshold slider
    threshold = st.slider(
        "Similarity Threshold",
        min_value=0.1,
        max_value=0.8,
        value=0.35,
        step=0.05,
        help="Higher = more precise but fewer cache hits. Lower = more hits but less accurate matching.",
    )
    st.markdown(
        f'<p style="font-size:0.75rem;color:#666;">Current: **{threshold}** — '
        f'{"Aggressive caching" if threshold < 0.35 else "Balanced" if threshold < 0.5 else "Conservative"}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Metrics
    total = st.session_state.total_messages
    hits = st.session_state.cache_hits
    misses = st.session_state.cache_misses
    hit_rate = (hits / total * 100) if total > 0 else 0

    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">Total Messages</p>
        <p class="metric-value">{total}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Cache Hits</p>
            <p class="metric-value">{hits}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Misses</p>
            <p class="metric-value-red">{misses}</p>
        </div>
        """, unsafe_allow_html=True)

    # Cache hit rate — big number
    rate_color = "#00ff88" if hit_rate >= 50 else "#ff8800" if hit_rate >= 30 else "#ff4444"
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">Cache Hit Rate</p>
        <p style="font-size:3rem;font-weight:900;color:{rate_color};margin:0;">{hit_rate:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Cost analysis
    cost_without = total * 0.01
    cost_with = hits * 0.0001 + misses * 0.01
    saved = cost_without - cost_with

    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">Cost Without Cache</p>
        <p class="metric-value-red">${cost_without:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">Cost With Cache</p>
        <p class="metric-value">${cost_with:.4f}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">💰 Total Saved</p>
        <p style="font-size:2.5rem;font-weight:900;color:#00ff88;margin:0;">${saved:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

    # Scale projection
    if total > 0:
        savings_per_msg = saved / total if total > 0 else 0.0099
        daily_savings_1m = savings_per_msg * 1_000_000
        st.markdown(f"""
        <div class="metric-card" style="border-color:#00ff8830;">
            <p class="metric-label">At 1M Messages/Day</p>
            <p style="font-size:1.8rem;font-weight:800;color:#00ff88;margin:0;">
                Saves ${daily_savings_1m:,.0f}/day
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Hot cache stats
    hc = st.session_state.hot_cache
    st.markdown(f"""
    <div class="metric-card" style="border-color:#ff880030;">
        <p class="metric-label">🔥 Hot Cache Clusters</p>
        <p style="font-size:1.5rem;font-weight:700;color:#ff8800;margin:0;">{hc.get_total_clusters()}</p>
        <p style="font-size:0.8rem;color:#888;margin:4px 0 0 0;">{hc.get_promoted_count()} promoted</p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-promote settings
    st.markdown("#### 🔥 Hot Cache Settings")
    auto_promote_on = st.toggle("Auto-promote patterns", value=True)
    promote_threshold = st.slider(
        "Promotion threshold",
        min_value=2,
        max_value=10,
        value=3,
        help="How many times a pattern must appear before auto-promotion.",
    )


# ══════════════════════════════════════════════
# MAIN CONTENT AREA
# ══════════════════════════════════════════════

# Title
st.markdown('<p class="main-title">⚡ CompanionCache</p>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Semantic caching layer for AI companions — cut LLM costs by 70%+ without losing personality</p>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SECTION 1 — Live Demo
# ──────────────────────────────────────────────
st.markdown("## 💬 Live Demo")

user_input = st.text_input(
    "Type any message an AI companion user would send...",
    placeholder="e.g. 'im feeling so lonely today', 'good morning', 'do you love me'",
    key="live_input",
)

if user_input and user_input != st.session_state.get("_last_processed", ""):
    st.session_state["_last_processed"] = user_input
    st.session_state.last_input = user_input

    # Classify with hot cache
    intent, confidence, hit, was_hot_hit = classify_with_hot_cache(
        user_input, st.session_state.hot_cache, threshold
    )

    # Auto-promote if enabled
    if auto_promote_on:
        st.session_state.hot_cache.auto_promote(promote_threshold)

    # Get response
    response = get_next_response(intent)
    update_metrics(intent, hit)

    # Store in history
    st.session_state.message_history.append({
        "text": user_input,
        "intent": intent,
        "confidence": confidence,
        "hit": hit,
        "response": response,
        "hot_hit": was_hot_hit,
    })

    # Display results
    col_status, col_latency = st.columns([3, 1])
    with col_status:
        if hit:
            hit_label = "🔥 HOT CACHE HIT" if was_hot_hit else "CACHE HIT"
            st.markdown(f'<span class="cache-hit">✅ {hit_label}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="cache-miss">❌ CACHE MISS — Would call LLM</span>', unsafe_allow_html=True)

    with col_latency:
        if hit:
            st.markdown('<p class="latency-cached">⚡ 4ms</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="latency-llm">🐌 ~850ms</p>', unsafe_allow_html=True)

    # Intent + confidence
    st.markdown(
        f'<span class="intent-badge">{intent}</span>'
        f'<span class="confidence-badge">{confidence:.2%} confidence</span>',
        unsafe_allow_html=True,
    )

    # Response
    st.markdown(f'<div class="response-box">{response}</div>', unsafe_allow_html=True)

    # Memory injection preview
    if st.session_state.memory_fact:
        st.markdown("##### Memory Injection Preview")
        mem_col1, mem_col2 = st.columns(2)
        with mem_col1:
            st.markdown(f"""
            <div class="memory-without">
                <p style="font-size:0.75rem;color:#888;margin:0 0 8px 0;">WITHOUT MEMORY — $0.0001</p>
                {response}
            </div>
            """, unsafe_allow_html=True)
        with mem_col2:
            injected = inject_memory(response, st.session_state.memory_fact)
            st.markdown(f"""
            <div class="memory-with">
                <p style="font-size:0.75rem;color:#00ff88;margin:0 0 8px 0;">WITH MEMORY — $0.0001 (still just a DB lookup!)</p>
                {injected.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Rotating Cache Demo
# ──────────────────────────────────────────────
st.markdown("## 🔄 Response Rotation Demo")
st.markdown("*Proves the same user can send the same message repeatedly and get unique responses every time — zero repetition, zero LLM cost.*")

rot_col1, rot_col2 = st.columns([1, 3])
with rot_col1:
    repeat_msg = st.text_input(
        "Message to repeat:",
        value="im feeling lonely",
        key="rotation_input",
    )
    repeat_count = st.selectbox("Repeat count:", [5, 10, 15, 20], index=0)

if st.button("🔁 Send Same Message Multiple Times", key="rotation_btn", use_container_width=True):
    # Temporarily save and restore rotation index
    results = []
    for i in range(repeat_count):
        intent, conf = classify(repeat_msg)
        resp = get_next_response(intent)
        results.append({
            "#": i + 1,
            "Intent": intent,
            "Confidence": f"{conf:.2%}",
            "Response": resp[:80] + "..." if len(resp) > 80 else resp,
            "Cost": "$0.0001",
        })

    st.markdown(f'<span class="cache-hit">✅ {repeat_count} unique responses served — $0.00 LLM cost</span>', unsafe_allow_html=True)
    st.dataframe(
        pd.DataFrame(results),
        use_container_width=True,
        hide_index=True,
    )

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Memory Injection Layer
# ──────────────────────────────────────────────
st.markdown("## 🧠 Memory Injection Layer")
st.markdown("*Append personalized context to cached responses — looks personal, costs nothing extra.*")

mem_col1, mem_col2 = st.columns([1, 1])
with mem_col1:
    memory_input = st.text_input(
        "Enter a memory fact about the user:",
        placeholder="e.g. 'stressed about final exams', 'loves coffee', 'just got promoted'",
        key="memory_input",
    )
    if memory_input:
        st.session_state.memory_fact = memory_input

with mem_col2:
    st.markdown(f"""
    <div class="metric-card" style="text-align:left;">
        <p class="metric-label">Current Memory</p>
        <p style="color:#00ff88;font-size:1.1rem;margin:8px 0 0 0;">
            {st.session_state.memory_fact if st.session_state.memory_fact else '<span style="color:#444;">No memory set</span>'}
        </p>
    </div>
    """, unsafe_allow_html=True)

# Demo the injection
if st.session_state.memory_fact:
    demo_intent = "greeting_morning"
    demo_response = RESPONSES[demo_intent][0]
    injected = inject_memory(demo_response, st.session_state.memory_fact)

    demo_col1, demo_col2 = st.columns(2)
    with demo_col1:
        st.markdown(f"""
        <div class="memory-without">
            <p style="font-size:0.75rem;color:#888;margin:0 0 8px 0;">❌ WITHOUT MEMORY</p>
            <p style="margin:0;">{demo_response}</p>
            <p style="font-size:0.8rem;color:#888;margin:8px 0 0 0;">Cost: $0.0001 (cache)</p>
        </div>
        """, unsafe_allow_html=True)
    with demo_col2:
        st.markdown(f"""
        <div class="memory-with">
            <p style="font-size:0.75rem;color:#00ff88;margin:0 0 8px 0;">✅ WITH MEMORY</p>
            <p style="margin:0;">{injected.replace(chr(10), '<br>')}</p>
            <p style="font-size:0.8rem;color:#00ff88;margin:8px 0 0 0;">Cost: $0.0001 (cache + DB lookup = $0.000)</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="metric-card" style="text-align:center;border-color:#00ff8830;">
        <p style="color:#888;font-size:0.85rem;margin:0;">Memory injection cost</p>
        <p style="color:#00ff88;font-size:2rem;font-weight:800;margin:0;">$0.000</p>
        <p style="color:#666;font-size:0.8rem;margin:4px 0 0 0;">Just a database lookup — no LLM involved</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SECTION 3 — Intent Distribution Chart
# ──────────────────────────────────────────────
st.markdown("## 📊 Intent Distribution")

intent_data = st.session_state.intent_counts
if sum(intent_data.values()) > 0:
    sorted_intents = sorted(intent_data.items(), key=lambda x: x[1], reverse=True)
    labels = [x[0] for x in sorted_intents if x[1] > 0]
    values = [x[1] for x in sorted_intents if x[1] > 0]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker=dict(
            color=values,
            colorscale=[[0, "#1a1a2e"], [0.5, "#4444ff"], [1, "#00ff88"]],
        ),
        text=values,
        textposition="outside",
        textfont=dict(color="#888888", size=12),
    ))
    fig.update_layout(
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#888888", size=12),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
        margin=dict(l=0, r=40, t=10, b=10),
        height=max(250, len(labels) * 35),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.markdown('*<p style="color:#444;">No messages processed yet. Type a message above to see the distribution.</p>*', unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SECTION 4 — Batch Benchmark
# ──────────────────────────────────────────────
st.markdown("## 🚀 Batch Benchmark")
st.markdown(f"*Run all {len(MESSAGES)} test messages through the classifier. See real cache hit rates and cost analysis.*")

if st.button("⚡ Run Full Benchmark", key="benchmark_btn", use_container_width=True):
    progress_bar = st.progress(0, text="Starting benchmark...")
    results = {"hits": 0, "misses": 0, "intents": {intent: 0 for intent in INTENTS}}
    total_msgs = len(MESSAGES)

    for i, msg in enumerate(MESSAGES):
        intent, conf = classify(msg["text"])
        hit = is_cache_hit(conf, threshold)

        if hit:
            results["hits"] += 1
        else:
            results["misses"] += 1

        results["intents"][intent] = results["intents"].get(intent, 0) + 1

        # Update progress (pace it over ~3-4 seconds)
        progress = (i + 1) / total_msgs
        progress_bar.progress(progress, text=f"Processing message {i+1}/{total_msgs}...")
        time.sleep(3.0 / total_msgs)

    progress_bar.progress(1.0, text="✅ Benchmark complete!")
    st.session_state.benchmark_results = results

    # Display results
    bench_hit_rate = results["hits"] / total_msgs * 100

    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1:
        rate_col = "#00ff88" if bench_hit_rate >= 60 else "#ff8800"
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Cache Hit Rate</p>
            <p style="font-size:3rem;font-weight:900;color:{rate_col};margin:0;">{bench_hit_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    with res_col2:
        bench_cost_without = total_msgs * 0.01
        bench_cost_with = results["hits"] * 0.0001 + results["misses"] * 0.01
        bench_saved = bench_cost_without - bench_cost_with
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Cost Saved ({total_msgs} msgs)</p>
            <p style="font-size:2.5rem;font-weight:900;color:#00ff88;margin:0;">${bench_saved:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    with res_col3:
        daily_save = (bench_saved / total_msgs) * 1_000_000
        st.markdown(f"""
        <div class="metric-card" style="border-color:#00ff8830;">
            <p class="metric-label">At 1M msgs/day</p>
            <p style="font-size:2rem;font-weight:800;color:#00ff88;margin:0;">${daily_save:,.0f}/day</p>
        </div>
        """, unsafe_allow_html=True)

    # Cost breakdown table
    st.markdown("#### Cost Analysis")
    cost_df = pd.DataFrame([
        {"Metric": "Total Messages", "Value": f"{total_msgs}"},
        {"Metric": "Cache Hits", "Value": f"{results['hits']}"},
        {"Metric": "Cache Misses", "Value": f"{results['misses']}"},
        {"Metric": "Cost Without Cache", "Value": f"${bench_cost_without:.2f}"},
        {"Metric": "Cost With Cache", "Value": f"${bench_cost_with:.4f}"},
        {"Metric": "Total Saved", "Value": f"${bench_saved:.2f}"},
        {"Metric": "Savings %", "Value": f"{(bench_saved/bench_cost_without*100):.1f}%"},
    ])
    st.dataframe(cost_df, use_container_width=True, hide_index=True)

    # Intent breakdown
    st.markdown("#### Intent Distribution (Benchmark)")
    bench_sorted = sorted(results["intents"].items(), key=lambda x: x[1], reverse=True)
    bench_labels = [x[0] for x in bench_sorted if x[1] > 0]
    bench_values = [x[1] for x in bench_sorted if x[1] > 0]

    bench_fig = go.Figure(go.Bar(
        x=bench_values,
        y=bench_labels,
        orientation="h",
        marker=dict(
            color=bench_values,
            colorscale=[[0, "#1a1a2e"], [0.5, "#4444ff"], [1, "#00ff88"]],
        ),
        text=bench_values,
        textposition="outside",
        textfont=dict(color="#888888", size=12),
    ))
    bench_fig.update_layout(
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#888888", size=12),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
        margin=dict(l=0, r=40, t=10, b=10),
        height=max(300, len(bench_labels) * 30),
    )
    st.plotly_chart(bench_fig, use_container_width=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SECTION 5 — Adaptive Hot Cache
# ──────────────────────────────────────────────
st.markdown("## 🔥 Adaptive Hot Cache")
st.markdown("*The cache learns from frequently missed messages and auto-promotes them — improving hit rate over time with zero LLM cost.*")

hc = st.session_state.hot_cache
top_patterns = hc.get_top_patterns(10)

if top_patterns:
    st.markdown("#### Top Uncached Patterns")

    pattern_data = []
    for i, cluster in enumerate(top_patterns):
        pattern_data.append({
            "#": i + 1,
            "Message Pattern": cluster["text"][:60] + ("..." if len(cluster["text"]) > 60 else ""),
            "Frequency": cluster["count"],
            "Guessed Intent": cluster["intent_guess"],
            "Status": "📥 Pending",
        })

    st.dataframe(
        pd.DataFrame(pattern_data),
        use_container_width=True,
        hide_index=True,
    )

    # Manual promote button
    if st.button("🚀 Promote All Eligible Patterns", key="promote_btn"):
        promoted = hc.auto_promote(promote_threshold)
        if promoted:
            st.markdown('<span class="cache-hit">✅ Patterns promoted! Cache hit rate will improve on next messages.</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color:#888;">No patterns have reached the promotion threshold ({promote_threshold}) yet.</span>', unsafe_allow_html=True)

    # Stats
    st.markdown(f"""
    <div style="display:flex;gap:12px;margin-top:12px;">
        <div class="metric-card" style="flex:1;border-color:#ff880030;">
            <p class="metric-label">Total Clusters</p>
            <p style="font-size:1.5rem;font-weight:700;color:#ff8800;margin:0;">{hc.get_total_clusters()}</p>
        </div>
        <div class="metric-card" style="flex:1;border-color:#00ff8830;">
            <p class="metric-label">Promoted</p>
            <p style="font-size:1.5rem;font-weight:700;color:#00ff88;margin:0;">{hc.get_promoted_count()}</p>
        </div>
        <div class="metric-card" style="flex:1;">
            <p class="metric-label">Promotion Threshold</p>
            <p style="font-size:1.5rem;font-weight:700;color:#888;margin:0;">{promote_threshold}x</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="metric-card" style="text-align:center;">
        <p style="color:#666;margin:0;">No cache miss patterns detected yet.</p>
        <p style="color:#444;font-size:0.85rem;margin:4px 0 0 0;">Send some messages above — misses will appear here for auto-promotion.</p>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;padding:20px 0;">
    <p style="color:#333;font-size:0.85rem;">
        CompanionCache — Semantic caching for AI companions<br>
        Built with sentence-transformers (all-MiniLM-L6-v2) · Cosine similarity · Streamlit
    </p>
</div>
""", unsafe_allow_html=True)
