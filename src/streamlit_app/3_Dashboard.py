import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import (set_ios_design, page_header, section_title,
                         skill_bar, performance_ring, kpi_grid, strengths_focus)
from src.config import DATA_DIR

set_ios_design()

@st.cache_data
def load_games():
    return pd.read_csv(DATA_DIR / "demo_games.csv")

games = load_games()

# Game selector
game_options = games["title"].tolist()
current_id = st.session_state.get("current_game_id")
if current_id in games["game_id"].values:
    default_index = game_options.index(games[games["game_id"] == current_id].iloc[0]["title"])
else:
    default_index = 0

selected_title = st.selectbox("Select Game", game_options, index=default_index, label_visibility="collapsed", key="dashboard_game_select")
game = games[games["title"] == selected_title].iloc[0]
game_id = int(game["game_id"])
st.session_state["current_game_id"] = game_id

page_header(selected_title, f"🏓 {game['sport']} · {game['date']} · {game['duration']}")

# Linked video preview
video_path = st.session_state.get("last_uploaded_video")
if video_path and Path(video_path).exists():
    st.video(video_path)
else:
    st.markdown(
        '<div class="nm-card" style="text-align:center;padding:16px;color:#8E8E93;font-size:13px;">'
        '🎥 No video linked to this session yet — import one from the Upload page.</div>',
        unsafe_allow_html=True
    )

# ── Per-game demo content (Skills / Highlights / Insights) ───────────
SKILLS_BY_GAME = {
    1: [
        ("Serve",      "🏓", 4.7, "green"),
        ("Return",     "↩️", 4.8, "green"),
        ("Third Shot", "🎯", 3.5, "blue"),
        ("Dinking",    "👆", 3.7, "blue"),
        ("Volleys",    "⚡", 4.1, "green"),
        ("Movement",   "🚶", 4.4, "green"),
    ],
    2: [
        ("Serve",      "🏓", 3.9, "blue"),
        ("Return",     "↩️", 3.6, "blue"),
        ("Third Shot", "🎯", 3.2, "orange"),
        ("Dinking",    "👆", 3.4, "orange"),
        ("Volleys",    "⚡", 3.8, "blue"),
        ("Movement",   "🚶", 4.0, "green"),
    ],
    3: [
        ("Serve",      "🏓", 4.9, "green"),
        ("Return",     "↩️", 4.6, "green"),
        ("Third Shot", "🎯", 4.2, "green"),
        ("Dinking",    "👆", 4.5, "green"),
        ("Volleys",    "⚡", 4.4, "green"),
        ("Movement",   "🚶", 4.7, "green"),
    ],
}

HIGHLIGHTS_BY_GAME = {
    1: [
        ("Powerful cross-court winner",  "0:45", "Winner",       "tag-winner"),
        ("23-shot rally",                "2:00", "Long rally",   "tag-rally"),
        ("Successful poach at net",      "3:00", "Attack",       "tag-attack"),
        ("Amazing defensive get",        "3:00", "Great defense","tag-defense"),
    ],
    2: [
        ("Unforced error at the kitchen","1:10", "Error",        "tag-defense"),
        ("Third shot drop winner",       "1:52", "Winner",       "tag-winner"),
        ("12-shot dink rally",           "2:40", "Long rally",   "tag-rally"),
        ("Late return, easy put-away",   "3:35", "Attack",       "tag-attack"),
    ],
    3: [
        ("Match-point ace serve",        "5:20", "Winner",       "tag-winner"),
        ("31-shot marathon rally",       "3:15", "Long rally",   "tag-rally"),
        ("Perfectly timed poach",        "2:05", "Attack",       "tag-attack"),
        ("Diving defensive save",        "4:40", "Great defense","tag-defense"),
    ],
}

INSIGHTS_BY_GAME = {
    1: [
        ("#34C759", "Strong serve performance"),
        ("#FF9500", "Focus on third shot consistency"),
        ("#007AFF", "Excellent court coverage"),
    ],
    2: [
        ("#FF9500", "Third shot and dinking need more consistency"),
        ("#FF3B30", "Too many unforced errors near the kitchen"),
        ("#007AFF", "Movement and footwork stayed solid throughout"),
    ],
    3: [
        ("#34C759", "Best overall rating of the season so far"),
        ("#34C759", "Very consistent dinking and net play"),
        ("#007AFF", "Serve placement created multiple direct winners"),
    ],
}

skills = SKILLS_BY_GAME.get(game_id, SKILLS_BY_GAME[1])
highlights = HIGHLIGHTS_BY_GAME.get(game_id, HIGHLIGHTS_BY_GAME[1])
insights = INSIGHTS_BY_GAME.get(game_id, INSIGHTS_BY_GAME[1])

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
    insights_html = "".join(
        f"""
      <div class="insight-item">
        <div class="insight-dot" style="background:{color};"></div>
        {text}
      </div>"""
        for color, text in insights
    )
    st.markdown(f'<div class="nm-card">{insights_html}</div>', unsafe_allow_html=True)

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
    for label, icon, score, color in skills:
        skill_bar(label, icon, score, 5.0, color)
    st.markdown('</div>', unsafe_allow_html=True)

    sorted_skills = sorted(skills, key=lambda s: s[2], reverse=True)
    strengths_focus(
        strengths=[(s[0], s[2]) for s in sorted_skills[:2]],
        focus_areas=[(s[0], s[2]) for s in sorted_skills[-2:]]
    )

# ────────────────────────────────────────────────────────────────────
# TAB 3 — HIGHLIGHTS
# ────────────────────────────────────────────────────────────────────
with tab_highlights:
    section_title("Game Highlights")
    st.markdown('<p class="page-subtitle">Key moments identified</p>', unsafe_allow_html=True)

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
