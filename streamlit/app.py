import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from src.config import APP_PAGE_TITLE, APP_PAGE_ICON, DEFAULT_SPORT

st.set_page_config(
    page_title=APP_PAGE_TITLE,
    page_icon=APP_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.design import SPORTS, page_header, section_title, set_ios_design, sport_label
from src.auth.login_page import render_login_page
from src.auth.session_manager import get_current_user, logout
from src.db.session import get_db_session
from src.services.match_service import get_user_matches

set_ios_design()

current_user = get_current_user()
if current_user is None:
    render_login_page()
    st.stop()

VALID_SPORTS = tuple(SPORTS.keys())
initial_sport = (
    current_user.preferred_sport
    if current_user.preferred_sport in VALID_SPORTS
    else (DEFAULT_SPORT if DEFAULT_SPORT in VALID_SPORTS else "pickleball")
)

st.session_state.setdefault("sport", initial_sport)
if st.session_state["sport"] not in VALID_SPORTS:
    st.session_state["sport"] = initial_sport

st.session_state.setdefault("current_game_id", None)
st.session_state.setdefault("route", "main")
st.session_state.setdefault("nav_radio", "👤 Me")
st.session_state.setdefault("show_sport_dialog", False)

if "nav_target" in st.session_state:
    st.session_state["nav_radio"] = st.session_state.pop("nav_target")
    st.session_state["route"] = "main"


def _on_tab_change():
    st.session_state["route"] = "main"


with st.sidebar:
    st.markdown(
        """
        <div class="nm-sidebar-brand">
          <div class="nm-sidebar-logo">🎾</div>
          <div>
            <div class="nm-sidebar-title">NextMove</div>
            <div class="nm-sidebar-subtitle">Smart Coach AI</div>
          </div>
        </div>
        <div class="nm-sidebar-section">Navigation</div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        ["👤 Me", "📚 Library", "⬆️ Upload"],
        label_visibility="collapsed",
        key="nav_radio",
        on_change=_on_tab_change,
    )

    sport = st.session_state["sport"]
    info = SPORTS[sport]
    st.markdown(
        f"""
        <div style="margin:20px 7px 0;padding:11px 12px;background:#F7F7F9;border-radius:10px;">
          <div style="font-size:10px;color:#8E8E93;text-transform:uppercase;letter-spacing:.06em;font-weight:650;">Current sport</div>
          <div style="font-size:13px;font-weight:600;margin-top:4px;">{info['icon']} {info['label']}</div>
        </div>
        <div class="nm-sidebar-account">{current_user.email}</div>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Choose your sport")
def _sport_selection_dialog():
    st.markdown(
        '<div style="font-size:24px;font-weight:700;text-align:center;margin-bottom:2px;">Let\'s go Buddy!</div>'
        '<div style="text-align:center;color:#8E8E93;margin-bottom:16px;">Choose your sport</div>',
        unsafe_allow_html=True,
    )

    current = st.session_state["sport"]
    choice = st.radio(
        "Sport",
        list(VALID_SPORTS),
        index=list(VALID_SPORTS).index(current),
        format_func=lambda value: f"{SPORTS[value]['icon']}  {SPORTS[value]['label']} — {SPORTS[value]['description']}",
        label_visibility="collapsed",
        key="sport_dialog_choice",
    )
    if st.button("Continue", type="primary", use_container_width=True, key="sport_dialog_continue"):
        st.session_state["sport"] = choice
        st.session_state["show_sport_dialog"] = False
        st.rerun()


def _load_matches():
    with get_db_session() as db:
        matches = get_user_matches(db, current_user.id)
        for match in matches:
            db.expunge(match)
    return matches


def _render_me():
    page_header("Me")

    sport = st.session_state["sport"]
    info = SPORTS[sport]
    matches = [m for m in _load_matches() if m.sport == sport]

    profile_col, progress_col = st.columns([0.85, 1.65], gap="large")

    with profile_col:
        st.markdown(
            f"""
            <div class="nm-card nm-profile-card" style="text-align:center;">
              <div style="width:68px;height:68px;border-radius:50%;background:rgba(52,199,89,.13);margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:34px;">👤</div>
              <div style="font-size:19px;font-weight:700;">Player Profile</div>
              <div style="font-size:12px;color:#8E8E93;margin-top:4px;overflow-wrap:anywhere;">{current_user.email}</div>
              <div style="margin-top:14px;">
                <span class="sport-badge" style="color:{info['color']};background:{info['color']}14;">{info['icon']} {info['label']}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with progress_col:
        section_title("Progress")
        if matches:
            completed = [m for m in matches if m.status == "ready" and m.rating is not None]
            completed_count = len([m for m in matches if m.status == "ready"])
            average_rating = sum(float(m.rating) for m in completed) / len(completed) if completed else 0.0

            stat1, stat2 = st.columns(2)
            with stat1:
                st.markdown(
                    f"""
                    <div class="nm-card" style="min-height:118px;">
                      <div style="font-size:18px;color:#34C759;">★</div>
                      <div style="font-size:28px;font-weight:750;margin-top:3px;">{average_rating:.1f}</div>
                      <div style="font-size:12px;color:#8E8E93;">Average Rating</div>
                      <div style="font-size:11px;color:#34C759;margin-top:4px;">+0.3</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with stat2:
                st.markdown(
                    f"""
                    <div class="nm-card" style="min-height:118px;">
                      <div style="font-size:18px;color:#FF9500;">🎥</div>
                      <div style="font-size:28px;font-weight:750;margin-top:3px;">{completed_count}</div>
                      <div style="font-size:12px;color:#8E8E93;">Games Analyzed</div>
                      <div style="font-size:11px;color:#34C759;margin-top:4px;">+{completed_count}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            action_col, _ = st.columns([1, 1.5])
            with action_col:
                if st.button("View Detailed Stats", use_container_width=True, key="view_detailed_stats"):
                    st.session_state["route"] = "detailed_stats"
                    st.rerun()
        else:
            st.markdown(
                """
                <div class="nm-card" style="min-height:180px;display:flex;align-items:center;justify-content:center;text-align:center;">
                  <div>
                    <div style="font-size:30px;margin-bottom:8px;">📊</div>
                    <div style="font-size:15px;font-weight:650;">No analyzed games yet</div>
                    <div style="font-size:12px;color:#8E8E93;margin-top:4px;">Your progress will appear here after your first analysis.</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    section_title("Settings")
    with st.container(key="settings_actions"):
        app_col, sport_col, logout_col, _ = st.columns([1, 1, 1, 2.4])
        with app_col:
            if st.button("⚙️ App Settings", use_container_width=True, key="open_settings"):
                st.session_state["route"] = "settings"
                st.rerun()
        with sport_col:
            if st.button("🏟️ Change Sport", use_container_width=True, key="change_sport"):
                st.session_state["show_sport_dialog"] = True
        with logout_col:
            if st.button("↩️ Log out", use_container_width=True, key="logout_button"):
                logout()
                st.rerun()

    if st.session_state["show_sport_dialog"]:
        _sport_selection_dialog()


def _render_settings():
    top_left, _ = st.columns([1, 5])
    with top_left:
        if st.button("‹ Me", key="settings_back"):
            st.session_state["route"] = "main"
            st.session_state["nav_radio"] = "👤 Me"
            st.rerun()

    page_header("Settings")
    sport = st.session_state["sport"]

    panel, _ = st.columns([1.2, 1.8])
    with panel:
        with st.container(key="settings_panel"):
            st.markdown(
                f"""
                <div class="settings-row">
                  <span>Current Sport</span>
                  <span style="margin-left:auto;color:#8E8E93;">{sport_label(sport)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("🏟️ Change Sport", use_container_width=True, key="settings_change_sport"):
                st.session_state["show_sport_dialog"] = True

            st.markdown(
                """
                <div style="font-size:11px;color:#8E8E93;text-transform:uppercase;letter-spacing:.06em;font-weight:650;margin:18px 0 7px;">About</div>
                <div class="settings-row">
                  <span>Version</span>
                  <span style="margin-left:auto;color:#8E8E93;">1.0.0</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.session_state["show_sport_dialog"]:
        _sport_selection_dialog()


def _render_detailed_stats():
    top_left, _ = st.columns([1, 5])
    with top_left:
        if st.button("‹ Me", key="detailed_back"):
            st.session_state["route"] = "main"
            st.session_state["nav_radio"] = "👤 Me"
            st.rerun()

    page_header("Detailed Statistics")
    st.markdown(
        """
        <div class="nm-card" style="text-align:center;padding:48px 20px;max-width:760px;">
          <div style="font-size:40px;margin-bottom:10px;">📊</div>
          <div style="font-size:19px;font-weight:650;">Coming soon...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


route = st.session_state["route"]

if route == "settings":
    _render_settings()
elif route == "detailed_stats":
    _render_detailed_stats()
elif route == "analysis":
    exec((ROOT / "src/streamlit_app/3_Dashboard.py").read_text(encoding="utf-8"))
elif route == "coach":
    exec((ROOT / "src/streamlit_app/4_AI_Analysis.py").read_text(encoding="utf-8"))
elif page == "👤 Me":
    _render_me()
elif page == "📚 Library":
    exec((ROOT / "src/streamlit_app/1_Library.py").read_text(encoding="utf-8"))
elif page == "⬆️ Upload":
    exec((ROOT / "src/streamlit_app/2_Upload.py").read_text(encoding="utf-8"))
