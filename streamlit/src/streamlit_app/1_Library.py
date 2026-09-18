import streamlit as st

from src.design import SPORTS, page_header, set_ios_design
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.match_service import delete_match, get_user_matches, mark_match_ready, CVPipelineError

set_ios_design()
page_header("Library", "Your recordings and analyses")

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


toolbar_search, toolbar_status, toolbar_summary = st.columns([2.4, 1.2, 1], gap="small")
with toolbar_search:
    query = st.text_input(
        "Search recordings",
        placeholder="Search games…",
        label_visibility="collapsed",
        key="library_search",
    )
with toolbar_status:
    status_filter = st.selectbox(
        "Status",
        ["All statuses", "Ready", "Pending", "Processing", "Failed"],
        label_visibility="collapsed",
        key="library_status_filter",
    )
with toolbar_summary:
    st.markdown(
        f'<div style="height:40px;display:flex;align-items:center;justify-content:flex-end;color:#8E8E93;font-size:12px;">{sport_info["icon"]} {sport_info["label"]} · {len(matches)} game{"s" if len(matches) != 1 else ""}</div>',
        unsafe_allow_html=True,
    )

filtered = matches
if query.strip():
    needle = query.strip().lower()
    filtered = [m for m in filtered if needle in (m.title or "").lower()]

if status_filter != "All statuses":
    status_value = status_filter.lower()
    filtered = [m for m in filtered if m.status == status_value]

if not matches:
    st.markdown(
        f"""
        <div style="text-align:center;padding:80px 20px 40px;">
          <div style="font-size:72px;line-height:1;margin-bottom:18px;">{sport_info['icon']}</div>
          <div style="font-size:21px;font-weight:650;">No {sport_info['label']} Recordings</div>
          <div style="font-size:13px;color:#8E8E93;margin-top:7px;max-width:330px;margin-left:auto;margin-right:auto;">
            Go to Upload to add your first game.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

if not filtered:
    st.markdown(
        '<div class="nm-card" style="text-align:center;color:#8E8E93;padding:28px;">No recordings match these filters.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

st.markdown(
    '<div class="desktop-list-head"><span>Game</span><span>Rating</span><span>Rallies</span><span>Status / actions</span></div>',
    unsafe_allow_html=True,
)

status_meta = {
    "pending": ("◷ Pending", "status-pending"),
    "processing": ("⚙ Processing", "status-processing"),
    "ready": ("✓ Ready", "status-ready"),
    "failed": ("✕ Failed", "status-failed"),
}

for match in filtered:
    status_text, status_class = status_meta.get(match.status, status_meta["pending"])
    date_str = match.match_date.strftime("%b %d, %Y · %H:%M") if match.match_date else ""
    duration_text = f" · {match.duration}" if match.duration else ""

    with st.container(key=f"match_row_{match.id}"):
        info_col, rating_col, rallies_col, action_col = st.columns([4, 1, 1, 1.35], gap="small")

        with info_col:
            st.markdown(
                f"""
                <div style="padding:3px 0 6px;">
                  <div class="game-card-title">{match.title}</div>
                  <div style="display:flex;align-items:center;gap:8px;margin-top:5px;flex-wrap:wrap;">
                    <span class="sport-badge" style="color:{sport_info['color']};background:{sport_info['color']}14;">
                      {sport_info['icon']} {sport_info['label']}
                    </span>
                    <span class="game-card-date">{date_str}{duration_text}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with rating_col:
            rating_value = f"{float(match.rating):.1f} ★" if match.status == "ready" and match.rating is not None else "—"
            st.markdown(
                f'<div style="padding-top:8px;font-size:14px;font-weight:650;">{rating_value}</div>',
                unsafe_allow_html=True,
            )

        with rallies_col:
            rallies_value = str(match.rallies or 0) if match.status == "ready" else "—"
            st.markdown(
                f'<div style="padding-top:8px;font-size:14px;font-weight:650;">{rallies_value}</div>',
                unsafe_allow_html=True,
            )

        with action_col:
            st.markdown(
                f'<div style="margin:3px 0 7px;"><span class="status-badge {status_class}">{status_text}</span></div>',
                unsafe_allow_html=True,
            )

            if match.status == "ready":
                if st.button("Open", type="primary", use_container_width=True, key=f"open_analysis_{match.id}"):
                    st.session_state["current_game_id"] = match.id
                    st.session_state["route"] = "analysis"
                    st.rerun()
            elif match.status == "pending":
                if st.button("Analyze", use_container_width=True, key=f"analyze_{match.id}"):
                    _analyze(match.id)
            elif match.status == "processing":
                st.progress(0.5)
            elif match.status == "failed":
                if st.button("Retry", use_container_width=True, key=f"retry_{match.id}"):
                    _analyze(match.id)

            with st.popover("•••", use_container_width=True):
                if match.status in ("pending", "failed"):
                    if st.button(
                        "✨ Analyze Now" if match.status == "pending" else "↻ Retry Analysis",
                        key=f"menu_analyze_{match.id}",
                        use_container_width=True,
                    ):
                        _analyze(match.id)
                if st.button("🗑 Delete", key=f"menu_delete_{match.id}", use_container_width=True):
                    _confirm_delete(match.id)
