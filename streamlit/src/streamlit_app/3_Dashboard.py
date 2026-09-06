import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import (set_ios_design, page_header, section_title,
                         skill_bar, performance_ring, kpi_grid, strengths_focus)
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.match_service import get_user_matches
from src.services.video_storage import get_video_url

set_ios_design()

current_user = get_current_user()

with get_db_session() as db:
    all_matches = get_user_matches(db, current_user.id)
    for m in all_matches:
        db.expunge(m)

ready_matches = [m for m in all_matches if m.status == "ready"]

if not ready_matches:
    page_header("Dashboard")
    st.markdown("""
    <div class="nm-card" style="text-align:center;padding:32px 20px;">
      <div style="font-size:32px;margin-bottom:8px;">📊</div>
      <div style="font-size:17px;font-weight:600;color:#1C1C1E;">No analyzed games yet</div>
      <div style="font-size:14px;color:#8E8E93;margin-top:4px;">Analyze a match from the Library to see its dashboard here.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Back to Library (façon push/pop de navigation iOS) ────────────────
if st.button("← Library", key="dashboard_back_to_library"):
    st.session_state["nav_target"] = "📚 Library"
    st.rerun()

# ── Game selector ───────────────────────────────────────────────────
match_by_title = {m.title: m for m in ready_matches}
titles = list(match_by_title.keys())

current_id = st.session_state.get("current_game_id")
default_index = 0
for i, m in enumerate(ready_matches):
    if m.id == current_id:
        default_index = i
        break

selected_title = st.selectbox(
    "Select Game", titles, index=default_index,
    label_visibility="collapsed", key="dashboard_game_select"
)
match = match_by_title[selected_title]
st.session_state["current_game_id"] = match.id

_sport_icons = {"pickleball": "🏓", "tennis": "🎾", "padel": "🥎"}
sport_icon = _sport_icons.get(match.sport, "🏓")
date_str = match.match_date.strftime("%b %d, %Y") if match.match_date else ""
page_header(selected_title, f"{sport_icon} {match.sport} · {date_str}")

# ── Linked video preview (URL signée depuis Supabase Storage) ────────
if match.video_storage_path:
    try:
        video_url = get_video_url(match.video_storage_path)
        st.video(video_url)
    except Exception:
        st.markdown(
            '<div class="nm-card" style="text-align:center;padding:16px;color:#8E8E93;font-size:13px;">'
            '🎥 Video temporarily unavailable.</div>',
            unsafe_allow_html=True
        )
else:
    st.markdown(
        '<div class="nm-card" style="text-align:center;padding:16px;color:#8E8E93;font-size:13px;">'
        '🎥 No video linked to this match.</div>',
        unsafe_allow_html=True
    )

skills = match.skills or []
highlights = match.highlights or []
insights = match.insights or []

# ── Tabs matching iOS app ─────────────────────────────────────────────
tab_overview, tab_skills, tab_highlights, tab_stats = st.tabs(
    ["Overview", "Skills", "Highlights", "Stats"]
)

# ────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ────────────────────────────────────────────────────────────────────
with tab_overview:
    performance_ring(float(match.rating), 5.0, "Overall Performance")

    label = "Strong Performance" if match.rating >= 4.0 else ("Good Performance" if match.rating >= 3.0 else "Keep Working")
    st.markdown(f"""
    <div style="text-align:center;margin:-8px 0 16px;">
      <span style="background:#EBF5FF;color:#007AFF;font-size:14px;font-weight:600;
                   padding:6px 16px;border-radius:20px;">👍 {label}</span>
    </div>
    """, unsafe_allow_html=True)

    section_title("Key Insights")
    insights_html = "".join(
        f"""
      <div class="insight-item">
        <div class="insight-dot" style="background:{i['color']};"></div>
        {i['text']}
      </div>""" for i in insights
    )
    st.markdown(f'<div class="nm-card">{insights_html}</div>', unsafe_allow_html=True)

    kpi_grid([
        ("🔄", match.rallies, "Rallies", "#1C1C1E"),
        ("🏆", match.winners, "Winners", "#34C759"),
        ("❌", match.errors, "Errors", "#FF3B30"),
        ("🏃", f"{match.coverage}%", "Coverage", "#007AFF"),
    ])

# ────────────────────────────────────────────────────────────────────
# TAB 2 — SKILLS
# ────────────────────────────────────────────────────────────────────
with tab_skills:
    section_title("Skill Breakdown")
    st.markdown('<p class="page-subtitle">Detailed performance by category</p>', unsafe_allow_html=True)

    st.markdown('<div class="nm-card">', unsafe_allow_html=True)
    for s in skills:
        skill_bar(s["label"], s["icon"], s["score"], 5.0, s["color"])
    st.markdown('</div>', unsafe_allow_html=True)

    sorted_skills = sorted(skills, key=lambda s: s["score"], reverse=True)
    if len(sorted_skills) >= 4:
        strengths_focus(
            strengths=[(s["label"], s["score"]) for s in sorted_skills[:2]],
            focus_areas=[(s["label"], s["score"]) for s in sorted_skills[-2:]]
        )

# ────────────────────────────────────────────────────────────────────
# TAB 3 — HIGHLIGHTS
# ────────────────────────────────────────────────────────────────────
with tab_highlights:
    section_title("Game Highlights")
    st.markdown('<p class="page-subtitle">Key moments identified</p>', unsafe_allow_html=True)

    st.markdown('<div class="nm-card">', unsafe_allow_html=True)
    for h in highlights:
        st.markdown(f"""
        <div class="highlight-row">
          <div>
            <div class="highlight-title">{h['title']}</div>
            <div class="highlight-time">{h['time']}</div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;">
            <span class="highlight-tag {h['tag_class']}">{h['tag']}</span>
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
        st.metric("Total Rallies", match.rallies)
        st.metric("Winners", match.winners)
        st.metric("Unforced Errors", match.errors)
    with col2:
        st.metric("Court Coverage", f"{match.coverage}%")
        st.metric("Overall Rating", match.rating)
        st.metric("Match Duration", match.duration or "N/A")

    if skills:
        section_title("Performance Radar")
        categories = [s["label"] for s in skills]
        scores = [s["score"] for s in skills]

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