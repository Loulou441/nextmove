import streamlit as st

from src.design import SPORTS, page_header, set_ios_design
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.match_service import delete_match, get_user_matches, mark_match_ready, CVPipelineError

set_ios_design()
page_header("Library")

current_user = get_current_user()
if current_user is None:
    st.stop()

sport = st.session_state.get("sport", "pickleball")
sport_info = SPORTS.get(sport, SPORTS["pickleball"])

with get_db_session() as db:
    all_matches = get_user_matches(db, current_user.id)
    matches = [m for m in all_matches if m.sport == sport]
    for match in matches:
        db.expunge(match)


@st.dialog("Delete Recording")
def _confirm_delete(match_id: str):
    st.write("This will permanently delete this recording and its analysis.")
    cancel_col, delete_col = st.columns(2)
    with cancel_col:
        if st.button("Cancel", use_container_width=True, key=f"cancel_delete_{match_id}"):
            st.rerun()
    with delete_col:
        if st.button("Delete", type="primary", use_container_width=True, key=f"confirm_delete_{match_id}"):
            with get_db_session() as db:
                delete_match(db, match_id, current_user.id)
            if st.session_state.get("current_game_id") == match_id:
                st.session_state["current_game_id"] = None
            st.rerun()


def _analyze(match_id: str):
    try:
        with st.spinner("Analyzing..."):
            with get_db_session() as db:
                mark_match_ready(db, match_id)
        st.rerun()
    except CVPipelineError as exc:
        st.error(f"Analysis failed: {exc}")
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")


if not matches:
    st.markdown(
        f"""
        <div style="text-align:center;padding:74px 20px 40px;">
          <div style="font-size:80px;line-height:1;margin-bottom:20px;">{sport_info['icon']}</div>
          <div style="font-size:22px;font-weight:650;">No {sport_info['label']} Recordings</div>
          <div style="font-size:14px;color:#8E8E93;margin-top:8px;max-width:330px;margin-left:auto;margin-right:auto;">
            Go to the Upload tab to record your first game
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

status_meta = {
    "pending": ("◷ Pending", "status-pending"),
    "processing": ("⚙ Processing", "status-processing"),
    "ready": ("✓ Ready", "status-ready"),
    "failed": ("✕ Failed", "status-failed"),
}

for match in matches:
    status_text, status_class = status_meta.get(match.status, status_meta["pending"])
    date_str = match.match_date.strftime("%b %d, %Y · %H:%M") if match.match_date else ""
    duration_text = f" · {match.duration}" if match.duration else ""

    st.markdown(
        f"""
        <div class="game-card">
          <div class="game-card-header">
            <div>
              <div class="game-card-title">{match.title}</div>
              <div style="display:flex;align-items:center;gap:8px;margin-top:6px;flex-wrap:wrap;">
                <span class="sport-badge" style="color:{sport_info['color']};background:{sport_info['color']}18;">
                  {sport_info['icon']} {sport_info['label']}
                </span>
                <span class="game-card-date">{date_str}{duration_text}</span>
              </div>
            </div>
            <span class="status-badge {status_class}">{status_text}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Le menu ••• de RecordingCard.swift devient un popover Streamlit.
    with st.popover("•••", use_container_width=False):
        if match.status in ("pending", "failed"):
            if st.button("✨ Analyze Now" if match.status == "pending" else "↻ Retry Analysis", key=f"menu_analyze_{match.id}", use_container_width=True):
                _analyze(match.id)
        if st.button("🗑 Delete", key=f"menu_delete_{match.id}", use_container_width=True):
            _confirm_delete(match.id)

    if match.status == "ready":
        col1, col2, col3 = st.columns(3)
        col1.metric("Rating", f"{float(match.rating or 0):.1f}")
        col2.metric("Rallies", match.rallies or 0)
        col3.metric("Winners", match.winners or 0)

        if st.button("View Analysis", type="primary", use_container_width=True, key=f"open_analysis_{match.id}"):
            st.session_state["current_game_id"] = match.id
            st.session_state["route"] = "analysis"
            st.rerun()

    elif match.status == "pending":
        if st.button("✨ Analyze Game", use_container_width=True, key=f"analyze_{match.id}"):
            _analyze(match.id)

    elif match.status == "processing":
        st.progress(0.5, text="Analyzing recording…")

    elif match.status == "failed":
        if st.button("↻ Retry Analysis", use_container_width=True, key=f"retry_{match.id}"):
            _analyze(match.id)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
