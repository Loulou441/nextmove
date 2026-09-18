import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from src.config import APP_PAGE_TITLE, APP_PAGE_ICON, DEFAULT_SPORT

st.set_page_config(
    page_title=APP_PAGE_TITLE,
    page_icon=APP_PAGE_ICON,
    layout="centered",
    initial_sidebar_state="collapsed",
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

# Navigation programmée depuis une page enfant.
if "nav_target" in st.session_state:
    st.session_state["nav_radio"] = st.session_state.pop("nav_target")
    st.session_state["route"] = "main"


def _on_tab_change():
    st.session_state["route"] = "main"


with st.container(key="bottom_nav"):
    page = st.radio(
        "Navigation",
        ["👤 Me", "📚 Library", "⬆️ Upload"],
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio",
        on_change=_on_tab_change,
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

    st.markdown(
        f"""
        <div class="nm-card" style="text-align:center;padding:24px 18px;">
          <div style="width:80px;height:80px;border-radius:50%;background:#34C759;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:42px;">👤</div>
          <div style="font-size:21px;font-weight:700;">Player Profile</div>
          <div style="font-size:14px;color:#8E8E93;margin-top:4px;">{current_user.email}</div>
          <div style="margin-top:14px;">
            <span class="sport-badge">{info['icon']} {info['label']}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    matches = [m for m in _load_matches() if m.sport == sport]
    if matches:
        section_title("Progress")
        completed = [m for m in matches if m.status == "ready" and m.rating is not None]
        completed_count = len([m for m in matches if m.status == "ready"])
        average_rating = (
            sum(float(m.rating) for m in completed) / len(completed)
            if completed
            else 0.0
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div class="nm-card" style="min-height:142px;">
                  <div style="font-size:22px;color:#34C759;">★</div>
                  <div style="font-size:29px;font-weight:750;margin-top:4px;">{average_rating:.1f}</div>
                  <div style="font-size:13px;color:#8E8E93;">Average Rating</div>
                  <div style="font-size:12px;color:#34C759;margin-top:5px;">+0.3</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="nm-card" style="min-height:142px;">
                  <div style="font-size:22px;color:#FF9500;">🎥</div>
                  <div style="font-size:29px;font-weight:750;margin-top:4px;">{completed_count}</div>
                  <div style="font-size:13px;color:#8E8E93;">Games Analyzed</div>
                  <div style="font-size:12px;color:#34C759;margin-top:5px;">+{completed_count}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("View Detailed Stats", use_container_width=True, key="view_detailed_stats"):
            st.session_state["route"] = "detailed_stats"
            st.rerun()

    section_title("Settings")
    if st.button("⚙️  App Settings    ›", use_container_width=True, key="open_settings"):
        st.session_state["route"] = "settings"
        st.rerun()

    if st.button("🏟️  Change Sport    ›", use_container_width=True, key="change_sport"):
        st.session_state["show_sport_dialog"] = True

    if st.button("↩️  Se déconnecter    ›", use_container_width=True, key="logout_button"):
        logout()
        st.rerun()

    if st.session_state["show_sport_dialog"]:
        _sport_selection_dialog()


def _render_settings():
    if st.button("‹ Me", key="settings_back"):
        st.session_state["route"] = "main"
        st.session_state["nav_radio"] = "👤 Me"
        st.rerun()

    st.markdown('<div style="text-align:center;font-size:18px;font-weight:650;margin:-36px 0 22px;">Settings</div>', unsafe_allow_html=True)
    sport = st.session_state["sport"]
    st.markdown(
        f"""
        <div class="nm-card" style="display:flex;align-items:center;justify-content:space-between;">
          <span>Current Sport</span>
          <span class="muted">{sport_label(sport)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🏟️  Change Sport", use_container_width=True, key="settings_change_sport"):
        st.session_state["show_sport_dialog"] = True

    section_title("About")
    st.markdown(
        '<div class="nm-card" style="display:flex;justify-content:space-between;"><span>Version</span><span class="muted">1.0.0</span></div>',
        unsafe_allow_html=True,
    )

    if st.session_state["show_sport_dialog"]:
        _sport_selection_dialog()


def _render_detailed_stats():
    if st.button("‹ Me", key="detailed_back"):
        st.session_state["route"] = "main"
        st.session_state["nav_radio"] = "👤 Me"
        st.rerun()
    st.markdown('<div style="text-align:center;font-size:18px;font-weight:650;margin:-36px 0 22px;">Detailed Statistics</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="nm-card" style="text-align:center;padding:54px 20px;">
          <div style="font-size:42px;margin-bottom:12px;">📊</div>
          <div style="font-size:20px;font-weight:650;">Coming soon...</div>
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
