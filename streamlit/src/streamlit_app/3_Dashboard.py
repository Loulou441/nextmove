import streamlit as st

from src.design import (
    SPORTS,
    kpi_grid,
    page_header,
    performance_ring,
    section_title,
    set_ios_design,
    skill_bar,
    strengths_focus,
)
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.match_service import get_user_matches
from src.services.video_storage import get_video_url

set_ios_design()
current_user = get_current_user()
if current_user is None:
    st.stop()

with get_db_session() as db:
    all_matches = get_user_matches(db, current_user.id)
    for item in all_matches:
        db.expunge(item)

ready_matches = [m for m in all_matches if m.status == "ready"]
current_id = st.session_state.get("current_game_id")
match = next((m for m in ready_matches if m.id == current_id), None)

if match is None:
    sport = st.session_state.get("sport", "pickleball")
    match = next((m for m in ready_matches if m.sport == sport), None)

if match is None:
    if st.button("‹ Library", key="analysis_empty_back"):
        st.session_state["route"] = "main"
        st.session_state["nav_radio"] = "📚 Library"
        st.rerun()
    page_header("Analysis")
    st.info("No analyzed game is available for this sport yet.")
    st.stop()

st.session_state["current_game_id"] = match.id
sport_info = SPORTS.get(match.sport, SPORTS["pickleball"])

back_col, title_col = st.columns([0.7, 5])
with back_col:
    if st.button("‹ Library", key="analysis_back"):
        st.session_state["route"] = "main"
        st.session_state["nav_radio"] = "📚 Library"
        st.rerun()
with title_col:
    date_str = match.match_date.strftime("%b %d, %Y") if match.match_date else ""
    page_header(match.title, f"{sport_info['icon']} {sport_info['label']} · {date_str}")

video_url = None
if match.video_storage_path:
    try:
        video_url = get_video_url(match.video_storage_path)
    except Exception:
        video_url = None

seek_key = f"analysis_seek_{match.id}"
st.session_state.setdefault(seek_key, 0)

skills = match.skills or []
highlights = match.highlights or []
rating = float(match.rating or 0)


def _rating_description(value: float) -> str:
    if value >= 4.5:
        return "Excellent Performance"
    if value >= 3.5:
        return "Strong Performance"
    if value >= 2.5:
        return "Good Performance"
    return "Room for Improvement"


def _time_to_seconds(value) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value or "0:00").strip()
    try:
        parts = [int(float(part)) for part in text.split(":")]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return int(float(text))
    except (TypeError, ValueError):
        return 0


video_col, summary_col = st.columns([1.7, 0.85], gap="large")

with video_col:
    if video_url:
        st.video(video_url, start_time=int(st.session_state[seek_key]))
    else:
        st.markdown(
            '<div class="nm-card" style="height:300px;display:flex;align-items:center;justify-content:center;color:#8E8E93;">🎥 Video temporarily unavailable.</div>',
            unsafe_allow_html=True,
        )

with summary_col:
    performance_ring(rating, 5.0, "Overall Performance")
    st.markdown(
        f'<div style="text-align:center;font-size:14px;font-weight:650;margin:-3px 0 11px;">{_rating_description(rating)}</div>',
        unsafe_allow_html=True,
    )
    if st.button("💬 Ask your AI Coach", type="primary", use_container_width=True, key="ask_ai_coach"):
        st.session_state["route"] = "coach"
        st.rerun()
    st.caption("Get personalized tips based on this game")

tab_overview, tab_skills, tab_highlights, tab_stats = st.tabs(
    ["Overview", "Skills", "Highlights", "Stats"]
)

with tab_overview:
    overview_left, overview_right = st.columns([1.1, 1], gap="large")
    with overview_left:
        section_title("💡 Key Insights")
        st.markdown(
            """
            <div class="nm-card">
              <div style="display:flex;gap:10px;margin:7px 0;font-size:13px;"><span style="color:#34C759;">↑</span><span>Strong serve performance</span></div>
              <div style="display:flex;gap:10px;margin:7px 0;font-size:13px;"><span style="color:#FF9500;">◎</span><span>Focus on third shot consistency</span></div>
              <div style="display:flex;gap:10px;margin:7px 0;font-size:13px;"><span style="color:#007AFF;">◉</span><span>Excellent court coverage</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with overview_right:
        section_title("Quick Stats")
        kpi_grid(
            [
                ("↔", match.rallies or 0, "Rallies", "#007AFF"),
                ("✓", match.winners or 0, "Winners", "#34C759"),
                ("✕", match.errors or 0, "Errors", "#FF3B30"),
                ("🚶", f"{match.coverage or 0}%", "Coverage", "#FF9500"),
            ]
        )

with tab_skills:
    section_title("Skill Breakdown")
    st.caption("Detailed performance by category")

    if not skills:
        st.info("No skill breakdown is available for this game.")
    else:
        skill_col, focus_col = st.columns([1.15, 0.85], gap="large")
        with skill_col:
            st.markdown('<div class="nm-card">', unsafe_allow_html=True)
            for skill in skills:
                skill_bar(
                    skill.get("label", "Skill"),
                    skill.get("icon", "•"),
                    skill.get("score", 0),
                    5.0,
                    skill.get("color", "green"),
                )
            st.markdown('</div>', unsafe_allow_html=True)

        with focus_col:
            ordered = sorted(skills, key=lambda item: float(item.get("score", 0)), reverse=True)
            if len(ordered) >= 4:
                strengths_focus(
                    [(s.get("label", "Skill"), float(s.get("score", 0))) for s in ordered[:2]],
                    [(s.get("label", "Skill"), float(s.get("score", 0))) for s in ordered[-2:]],
                )

with tab_highlights:
    section_title("Game Highlights")
    st.caption(f"{len(highlights)} key moments identified")

    if not highlights:
        st.markdown(
            '<div class="nm-card" style="text-align:center;color:#8E8E93;padding:28px;">No highlights detected for this game.</div>',
            unsafe_allow_html=True,
        )
    else:
        for idx, highlight in enumerate(highlights):
            left, right = st.columns([6, 0.8])
            with left:
                title = highlight.get("title", "Highlight")
                time_value = highlight.get("time", "0:00")
                tag = highlight.get("tag", "Moment")
                st.markdown(
                    f"""
                    <div class="nm-card nm-compact-card" style="margin-bottom:4px;">
                      <div style="font-size:14px;font-weight:600;">{title}</div>
                      <div style="font-size:11px;color:#8E8E93;margin-top:3px;">{time_value} · {tag}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with right:
                if st.button("▶", key=f"seek_{match.id}_{idx}", use_container_width=True):
                    st.session_state[seek_key] = _time_to_seconds(highlight.get("time"))
                    st.rerun()

with tab_stats:
    section_title("Detailed Statistics")
    st.caption("Complete game breakdown")

    rows = [
        ("↔", "Total Rallies", str(match.rallies or 0)),
        ("▥", "Longest Rally", "—"),
        ("✓", "Winners", str(match.winners or 0)),
        ("✕", "Unforced Errors", str(match.errors or 0)),
        ("⚡", "Attacks Attempted", "—"),
        ("◎", "Attacks Successful", "—"),
        ("%", "Attack Success Rate", "—"),
        ("🚶", "Court Coverage", f"{match.coverage or 0}%"),
    ]
    rows_html = ""
    for idx, (icon, label, value) in enumerate(rows):
        border = "border-bottom:1px solid #E5E5EA;" if idx < len(rows) - 1 else ""
        rows_html += (
            f'<div style="display:flex;align-items:center;gap:11px;padding:11px 0;{border}">'
            f'<span style="width:22px;color:#007AFF;">{icon}</span>'
            f'<span style="font-size:13px;">{label}</span>'
            f'<span style="margin-left:auto;font-size:13px;font-weight:600;">{value}</span>'
            '</div>'
        )
    st.markdown(f'<div class="nm-card" style="max-width:760px;">{rows_html}</div>', unsafe_allow_html=True)
