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
        background-color: #000000;
        color: #e0e0e0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 400 !important;
        letter-spacing: -0.01em;
    }

    /* Main title */
    .main-title {
        font-size: 2.5rem;
        font-weight: 300;
        color: #ffffff;
        margin-bottom: 0;
        letter-spacing: -0.03em;
    }
    .main-subtitle {
        font-size: 1rem;
        color: #888888;
        margin-top: 0;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* Cache status badges */
    .cache-hit {
        background: #ffffff;
        border: 1px solid #ffffff;
        color: #000000;
        padding: 6px 16px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .cache-miss {
        background: transparent;
        border: 1px solid #555555;
        color: #aaaaaa;
        padding: 6px 16px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Metric cards */
    .metric-card {
        background: transparent;
        border: 1px solid #333333;
        border-radius: 4px;
        padding: 24px;
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 300;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .metric-value-red {
        font-size: 2.5rem;
        font-weight: 300;
        color: #888888;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #666666;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* Response box */
    .response-box {
        background: #0a0a0a;
        border-left: 2px solid #ffffff;
        padding: 16px 20px;
        margin: 12px 0;
        font-size: 1.1rem;
        line-height: 1.5;
        color: #dddddd;
        font-weight: 300;
    }

    /* Intent badge */
    .intent-badge {
        background: transparent;
        border: 1px solid #444444;
        color: #cccccc;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 400;
        font-size: 0.8rem;
        display: inline-block;
        margin-right: 8px;
    }
    .confidence-badge {
        background: transparent;
        color: #888888;
        font-weight: 400;
        font-size: 0.8rem;
        display: inline-block;
    }

    /* Latency comparison */
    .latency-cached {
        color: #ffffff;
        font-weight: 300;
        font-size: 1.5rem;
    }
    .latency-llm {
        color: #666666;
        font-weight: 300;
        font-size: 1.5rem;
    }

    /* Memory injection boxes */
    .memory-without {
        background: transparent;
        border: 1px dashed #333333;
        border-radius: 4px;
        padding: 20px;
        color: #888888;
        font-weight: 300;
    }
    .memory-with {
        background: #0a0a0a;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 20px;
        color: #ffffff;
        font-weight: 300;
    }

    /* Section dividers */
    .section-divider {
        border: none;
        border-top: 1px solid #222222;
        margin: 3rem 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #050505;
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
    st.markdown('<p style="font-size:1.4rem;font-weight:300;color:#ffffff;margin-bottom:0;letter-spacing:-0.02em;">CompanionCache</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.85rem;color:#666666;margin-top:0;">Semantic Caching Dashboard</p>', unsafe_allow_html=True)
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
        f'<p style="font-size:0.75rem;color:#666;">Current matching strictness: **{threshold}**</p>',
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
        <p class="metric-label">Total Volume</p>
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
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">Cache Hit Rate</p>
        <p style="font-size:3rem;font-weight:300;color:#ffffff;margin:0;letter-spacing:-0.02em;">{hit_rate:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Cost analysis
    cost_without = total * 0.01
    cost_with = hits * 0.0001 + misses * 0.01
    saved = cost_without - cost_with

    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">LLM Cost Estimate</p>
        <p class="metric-value-red">${cost_without:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-label">Cache Cost</p>
        <p class="metric-value">${cost_with:.4f}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card" style="border-color:#555555;">
        <p class="metric-label" style="color:#ffffff;">Net Savings</p>
        <p style="font-size:2.5rem;font-weight:400;color:#ffffff;margin:0;letter-spacing:-0.02em;">${saved:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

    # Scale projection
    if total > 0:
        savings_per_msg = saved / total if total > 0 else 0.0099
        daily_savings_1m = savings_per_msg * 1_000_000
        st.markdown(f"""
        <div class="metric-card" style="border-color:#ffffff;">
            <p class="metric-label">At 1M Scale</p>
            <p style="font-size:1.5rem;font-weight:400;color:#ffffff;margin:0;letter-spacing:-0.01em;">
                Saves ${daily_savings_1m:,.0f}/day
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Hot cache stats
    hc = st.session_state.hot_cache
    st.markdown(f"""
    <div class="metric-card" style="border-color:#444444;">
        <p class="metric-label" style="color:#aaaaaa;">Adaptive Clusters</p>
        <p style="font-size:1.5rem;font-weight:300;color:#ffffff;margin:0;">{hc.get_total_clusters()}</p>
        <p style="font-size:0.8rem;color:#666;margin:4px 0 0 0;">{hc.get_promoted_count()} promoted</p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-promote settings
    st.markdown("#### Adaptive Settings")
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
st.markdown('<p class="main-title">CompanionCache</p>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Semantic caching layer for AI companions. Cut latency and cost instantly.</p>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SECTION 1 — Live Demo
# ──────────────────────────────────────────────
st.markdown("## Interactive Demo")

user_input = st.text_input(
    "Test real-time classification and retrieval",
    placeholder="e.g. 'im feeling so lonely today', 'good morning'",
    key="live_input",
    label_visibility="collapsed"
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
            hit_label = "ADAPTIVE HIT" if was_hot_hit else "CACHE HIT"
            st.markdown(f'<span class="cache-hit">{hit_label}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="cache-miss">CACHE MISS / LLM ROUTED</span>', unsafe_allow_html=True)

    with col_latency:
        if hit:
            st.markdown('<p class="latency-cached">4ms</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="latency-llm">~850ms</p>', unsafe_allow_html=True)

    # Intent + confidence
    st.markdown(
        f'<span class="intent-badge">{intent}</span>'
        f'<span class="confidence-badge">{confidence:.0%} match</span>',
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
                <p style="font-size:0.75rem;color:#888;margin:0 0 8px 0;letter-spacing:0.05em;text-transform:uppercase;">Without Memory Injection</p>
                {response}
            </div>
            """, unsafe_allow_html=True)
        with mem_col2:
            injected = inject_memory(response, st.session_state.memory_fact)
            st.markdown(f"""
            <div class="memory-with">
                <p style="font-size:0.75rem;color:#aaa;margin:0 0 8px 0;letter-spacing:0.05em;text-transform:uppercase;">With Context Appended</p>
                {injected.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Rotating Cache Demo
# ──────────────────────────────────────────────
st.markdown("## Response Rotation")
st.markdown("*Maintains illusion of live status by serving sequential responses to identical inputs.*")

rot_col1, rot_col2 = st.columns([1, 3])
with rot_col1:
    repeat_msg = st.text_input(
        "Input to repeat:",
        value="im feeling lonely",
        key="rotation_input",
    )
    repeat_count = st.selectbox("Iterations:", [5, 10, 15, 20], index=0)

if st.button("Simulate Repeated Input", key="rotation_btn", use_container_width=True):
    # Temporarily save and restore rotation index
    results = []
    for i in range(repeat_count):
        intent, conf = classify(repeat_msg)
        resp = get_next_response(intent)
        results.append({
            "#": i + 1,
            "Intent": intent,
            "Match": f"{conf:.0%}",
            "Response Fragment": resp[:80] + "..." if len(resp) > 80 else resp,
        })

    st.markdown(f'<span style="color:#ffffff;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;">{repeat_count} cache hits generated</span>', unsafe_allow_html=True)
    st.dataframe(
        pd.DataFrame(results),
        use_container_width=True,
        hide_index=True,
    )

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Memory Injection Layer
# ──────────────────────────────────────────────
st.markdown("## Context Injection")
st.markdown("*Append external database retrievals to cached templates.*")

mem_col1, mem_col2 = st.columns([1, 1])
with mem_col1:
    memory_input = st.text_input(
        "User context flag:",
        placeholder="e.g. 'stressed about final exams'",
        key="memory_input",
    )
    if memory_input:
        st.session_state.memory_fact = memory_input

with mem_col2:
    st.markdown(f"""
    <div class="metric-card" style="text-align:left;">
        <p class="metric-label">Active Context</p>
        <p style="color:#ffffff;font-size:1.1rem;margin:8px 0 0 0;font-weight:300;">
            {st.session_state.memory_fact if st.session_state.memory_fact else '<span style="color:#444;">Null</span>'}
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
            <p style="font-size:0.75rem;color:#666;margin:0 0 8px 0;letter-spacing:0.05em;text-transform:uppercase;">Null Context</p>
            <p style="margin:0;">{demo_response}</p>
            <p style="font-size:0.8rem;color:#555;margin:8px 0 0 0;">Cost coefficient: 1.0x</p>
        </div>
        """, unsafe_allow_html=True)
    with demo_col2:
        st.markdown(f"""
        <div class="memory-with">
            <p style="font-size:0.75rem;color:#aaa;margin:0 0 8px 0;letter-spacing:0.05em;text-transform:uppercase;">Context Appended</p>
            <p style="margin:0;">{injected.replace(chr(10), '<br>')}</p>
            <p style="font-size:0.8rem;color:#888;margin:8px 0 0 0;">Cost coefficient: 1.0x</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="metric-card" style="text-align:center;border-color:#333333;">
        <p style="color:#666;font-size:0.75rem;letter-spacing:0.05em;text-transform:uppercase;margin:0;">Processing Cost Delta</p>
        <p style="color:#ffffff;font-size:2rem;font-weight:300;margin:0;">$0.000</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SECTION 3 — Intent Distribution Chart
# ──────────────────────────────────────────────
st.markdown("## Query Classification")

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
            colorscale=[[0, "#222222"], [1, "#ffffff"]],
        ),
        text=values,
        textposition="outside",
        textfont=dict(color="#888888", size=12),
    ))
    fig.update_layout(
        plot_bgcolor="#000000",
        paper_bgcolor="#000000",
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
st.markdown("## Latency & Financial Impact Model")
st.markdown(f"*Simulating analysis over {len(MESSAGES)} natural language inputs.*")

if st.button("Initialize Benchmark", key="benchmark_btn", use_container_width=True):
    progress_bar = st.progress(0, text="Executing benchmark protocol...")
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
        progress_bar.progress(progress, text=f"Processing {i+1}/{total_msgs}...")
        time.sleep(3.0 / total_msgs)

    progress_bar.progress(1.0, text="Benchmark complete")
    st.session_state.benchmark_results = results

    # Display results
    bench_hit_rate = results["hits"] / total_msgs * 100

    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Cache Intercept Rate</p>
            <p style="font-size:2.5rem;font-weight:300;color:#ffffff;margin:0;letter-spacing:-0.02em;">{bench_hit_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    with res_col2:
        bench_cost_without = total_msgs * 0.01
        bench_cost_with = results["hits"] * 0.0001 + results["misses"] * 0.01
        bench_saved = bench_cost_without - bench_cost_with
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Cost Reduction ({total_msgs})</p>
            <p style="font-size:2.5rem;font-weight:300;color:#ffffff;margin:0;letter-spacing:-0.02em;">${bench_saved:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    with res_col3:
        daily_save = (bench_saved / total_msgs) * 1_000_000
        st.markdown(f"""
        <div class="metric-card" style="border-color:#555555;">
            <p class="metric-label">Projected Daily Savings</p>
            <p style="font-size:2.5rem;font-weight:400;color:#ffffff;margin:0;letter-spacing:-0.02em;">${daily_save:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)

    # Cost breakdown table
    st.markdown("#### Performance Matrix")
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
            colorscale=[[0, "#222222"], [1, "#ffffff"]],
        ),
        text=bench_values,
        textposition="outside",
        textfont=dict(color="#888888", size=12),
    ))
    bench_fig.update_layout(
        plot_bgcolor="#000000",
        paper_bgcolor="#000000",
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
st.markdown("## Adaptive Learning Protocol")
st.markdown("*Autonomous self-optimization of cache pathways.*")

hc = st.session_state.hot_cache
top_patterns = hc.get_top_patterns(10)

if top_patterns:
    st.markdown("#### Pending Optimization Nodes")

    pattern_data = []
    for i, cluster in enumerate(top_patterns):
        pattern_data.append({
            "#": i + 1,
            "Target Pattern": cluster["text"][:60] + ("..." if len(cluster["text"]) > 60 else ""),
            "Freq": cluster["count"],
            "Hypothesized Intent": cluster["intent_guess"],
            "Status": "Queue",
        })

    st.dataframe(
        pd.DataFrame(pattern_data),
        use_container_width=True,
        hide_index=True,
    )

    # Manual promote button
    if st.button("Execute Manual Promotion", key="promote_btn"):
        promoted = hc.auto_promote(promote_threshold)
        if promoted:
            st.markdown('<span style="color:#ffffff;">Optimization complete. Pathways updated.</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color:#666;">Metrics insufficient for threshold ({promote_threshold}).</span>', unsafe_allow_html=True)

    # Stats
    st.markdown(f"""
    <div style="display:flex;gap:12px;margin-top:12px;">
        <div class="metric-card" style="flex:1;border-color:#333;">
            <p class="metric-label">Detected Clusters</p>
            <p style="font-size:1.5rem;font-weight:300;color:#ffffff;margin:0;">{hc.get_total_clusters()}</p>
        </div>
        <div class="metric-card" style="flex:1;border-color:#555;">
            <p class="metric-label">Promoted Pathways</p>
            <p style="font-size:1.5rem;font-weight:300;color:#ffffff;margin:0;">{hc.get_promoted_count()}</p>
        </div>
        <div class="metric-card" style="flex:1;">
            <p class="metric-label">Activation Threshold</p>
            <p style="font-size:1.5rem;font-weight:300;color:#888;margin:0;">{promote_threshold}x</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="metric-card" style="text-align:center;">
        <p style="color:#888;margin:0;font-weight:300;">System is currently operating at optimization equilibrium.</p>
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
