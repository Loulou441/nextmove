import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from src.design import (set_ios_design, page_header, section_title,
                         skill_bar, performance_ring, kpi_grid, strengths_focus)

set_ios_design()

DATA_DIR = ROOT / "data"

@st.cache_data
def load_games():
    return pd.read_csv(DATA_DIR / "demo_games.csv")

games = load_games()

# Game selector
game_options = games["title"].tolist()
selected_title = st.selectbox("Select Game", game_options, label_visibility="collapsed")
game = games[games["title"] == selected_title].iloc[0]

page_header(selected_title, f"🏓 {game['sport']} · {game['date']} · {game['duration']}")

# ── Tabs matching iOS app ─────────────────────────────────────────────
tab_overview, tab_skills, tab_highlights, tab_stats = st.tabs(
    ["Overview", "Skills", "Highlights", "Stats"]
)

# ────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ────────────────────────────────────────────────────────────────────
with tab_overview:

    # Performance ring
    performance_ring(float(game["rating"]), 5.0, "Overall Performance")

    # Badge label
    label = "Strong Performance" if game["rating"] >= 4.0 else ("Good Performance" if game["rating"] >= 3.0 else "Keep Working")
    badge_color = "#007AFF"
    st.markdown(f"""
    <div style="text-align:center;margin:-8px 0 16px;">
      <span style="background:#EBF5FF;color:{badge_color};font-size:14px;font-weight:600;
                   padding:6px 16px;border-radius:20px;">👍 {label}</span>
    </div>
    """, unsafe_allow_html=True)

    # Key insights
    section_title("Key Insights")
    st.markdown("""
    <div class="nm-card">
      <div class="insight-item">
        <div class="insight-dot" style="background:#34C759;"></div>
        Strong serve performance
      </div>
      <div class="insight-item">
        <div class="insight-dot" style="background:#FF9500;"></div>
        Focus on third shot consistency
      </div>
      <div class="insight-item">
        <div class="insight-dot" style="background:#007AFF;"></div>
        Excellent court coverage
      </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI grid
    kpi_grid([
        ("🔄", int(game["rallies"]), "Rallies", "#1C1C1E"),
        ("🏆", int(game["winners"]), "Winners", "#34C759"),
        ("❌", int(game["errors"]),  "Errors",  "#FF3B30"),
        ("🏃", f"{int(game['coverage'])}%", "Coverage", "#007AFF"),
    ])

# ────────────────────────────────────────────────────────────────────
# TAB 2 — SKILLS
# ────────────────────────────────────────────────────────────────────
with tab_skills:
    section_title("Skill Breakdown")
    st.markdown('<p class="page-subtitle">Detailed performance by category</p>', unsafe_allow_html=True)

    st.markdown('<div class="nm-card">', unsafe_allow_html=True)
    skills = [
        ("Serve",       "🏓", 4.7, "green"),
        ("Return",      "↩️", 4.8, "green"),
        ("Third Shot",  "🎯", 3.5, "blue"),
        ("Dinking",     "👆", 3.7, "blue"),
        ("Volleys",     "⚡", 4.1, "green"),
        ("Movement",    "🚶", 4.4, "green"),
    ]
    for label, icon, score, color in skills:
        skill_bar(label, icon, score, 5.0, color)
    st.markdown('</div>', unsafe_allow_html=True)

    strengths_focus(
        strengths=[("Return", 4.8), ("Serve", 4.7)],
        focus_areas=[("Third Shot", 3.5), ("Dinking", 3.7)]
    )

# ────────────────────────────────────────────────────────────────────
# TAB 3 — HIGHLIGHTS
# ────────────────────────────────────────────────────────────────────
with tab_highlights:
    section_title("Game Highlights")
    st.markdown('<p class="page-subtitle">Key moments identified</p>', unsafe_allow_html=True)

    highlights = [
        ("Powerful cross-court winner", "0:45", "Winner",      "tag-winner"),
        ("23-shot rally",               "2:00", "Long rally",  "tag-rally"),
        ("Successful poach at net",     "3:00", "Attack",      "tag-attack"),
        ("Amazing defensive get",       "3:00", "Great defense","tag-defense"),
    ]

    st.markdown('<div class="nm-card">', unsafe_allow_html=True)
    for title, time_str, tag, tag_class in highlights:
        st.markdown(f"""
        <div class="highlight-row">
          <div>
            <div class="highlight-title">{title}</div>
            <div class="highlight-time">{time_str}</div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;">
            <span class="highlight-tag {tag_class}">{tag}</span>
            <span style="color:#007AFF;font-size:20px;">▶</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────
# TAB 4 — STATS
# ────────────────────────────────────────────────────────────────────
with tab_stats:
    section_title("Match Statistics")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Rallies",    int(game["rallies"]))
        st.metric("Winners",          int(game["winners"]))
        st.metric("Unforced Errors",  int(game["errors"]))
    with col2:
        st.metric("Court Coverage",   f"{int(game['coverage'])}%")
        st.metric("Overall Rating",   float(game["rating"]))
        st.metric("Match Duration",   game["duration"])

    # Radar chart
    section_title("Performance Radar")
    categories = ["Serve", "Return", "Third Shot", "Dinking", "Volleys", "Movement"]
    scores     = [4.7,     4.8,      3.5,          3.7,       4.1,       4.4]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="Performance",
        line_color="#007AFF",
        fillcolor="rgba(0,122,255,0.15)"
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], color="#8E8E93", gridcolor="#E5E5EA"),
            angularaxis=dict(color="#3C3C43"),
            bgcolor="rgba(0,0,0,0)"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=30, r=30, t=20, b=20),
        height=320,
        font=dict(family="DM Sans", color="#1C1C1E")
    )
    st.plotly_chart(fig, use_container_width=True)
