import os
import sys
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from src.config import APP_PAGE_TITLE, APP_PAGE_ICON, DEFAULT_SPORT

st.set_page_config(
    page_title=APP_PAGE_TITLE,
    page_icon=APP_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.design import set_ios_design, section_title, page_header

set_ios_design()

# ── Authentification : bloque tout accès tant que non connecté ────────
from src.auth.session_manager import get_current_user, logout
from src.auth.login_page import render_login_page
from src.db.session import get_db_session
from src.services.match_service import get_user_matches

current_user = get_current_user()

if current_user is None:
    render_login_page()
    st.stop()

# ── Shared session state defaults ────────────────────────────────────
st.session_state.setdefault("sport", DEFAULT_SPORT)
st.session_state.setdefault("current_game_id", None)

# Apply any pending navigation request BEFORE the radio widget is instantiated
# (session_state for a widget's key can't be set after that widget has rendered).
if "nav_target" in st.session_state:
    st.session_state["nav_radio"] = st.session_state.pop("nav_target")

# ── Barre de navigation en bas ──────────────────────────────────────
with st.container(key="bottom_nav"):
    page = st.radio(
        "Navigation",
        [
            "👤 Me",
            "📚 Library",
            "⬆️ Upload",
            "📊 Dashboard",
            "🧠 AI Analysis",
            "📈 Patterns",
            "📋 Training Plan",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio",
    )

# ── Route pages ──────────────────────────────────────────────────────
if page == "👤 Me":
    page_header("Me")

    _sport_labels = {"pickleball": "🏓 Pickleball", "tennis": "🎾 Tennis", "padel": "🥎 Padel"}
    sport_label = _sport_labels.get(st.session_state["sport"], "🏓 Pickleball")

    # Profile card
    st.markdown(f"""
    <div class="nm-card" style="text-align:center;padding:28px 20px;">
      <div style="width:72px;height:72px;background:#34C759;border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:32px;">👤</div>
      <div style="font-size:20px;font-weight:700;color:#1C1C1E;">Player Profile</div>
      <div class="sport-badge" style="margin:8px auto 0;width:fit-content;">{sport_label}</div>
    </div>
    """, unsafe_allow_html=True)

    section_title("Progress")

    with get_db_session() as db:
        _matches = get_user_matches(db, current_user.id)
        _ready_matches = [m for m in _matches if m.status == "ready"]
        games_analyzed = len(_ready_matches)
        average_rating = (
            round(sum(m.rating for m in _ready_matches) / games_analyzed, 1)
            if games_analyzed else 0.0
        )

        # "+N" = ce que ces indicateurs sont censés représenter : l'activité
        # récente, pas un chiffre inventé. Semaine glissante de 7 jours,
        # basée sur created_at (toujours renseigné, contrairement à
        # match_date qui peut être nul).
        _week_ago = datetime.utcnow() - timedelta(days=7)
        _recent = [m for m in _ready_matches if m.created_at and m.created_at >= _week_ago]
        _older = [m for m in _ready_matches if m.created_at and m.created_at < _week_ago]

        games_delta = len(_recent)

        rating_delta = None
        if _recent and _older:
            recent_avg = sum(m.rating for m in _recent) / len(_recent)
            older_avg = sum(m.rating for m in _older) / len(_older)
            rating_delta = round(recent_avg - older_avg, 1)

    rating_delta_html = ""
    if rating_delta is not None:
        _color = "#34C759" if rating_delta >= 0 else "#FF3B30"
        _sign = "+" if rating_delta >= 0 else ""
        rating_delta_html = f'<div style="font-size:12px;color:{_color};margin-top:4px;">{_sign}{rating_delta} vs. la semaine dernière</div>'

    games_delta_html = ""
    if games_delta > 0:
        games_delta_html = f'<div style="font-size:12px;color:#34C759;margin-top:4px;">+{games_delta} cette semaine</div>'

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="nm-card">
          <div style="font-size:22px;margin-bottom:4px;">⭐</div>
          <div style="font-size:32px;font-weight:700;color:#1C1C1E;">{average_rating}</div>
          <div style="font-size:13px;color:#8E8E93;">Average Rating</div>
          {rating_delta_html}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="nm-card">
          <div style="font-size:22px;margin-bottom:4px;">🎬</div>
          <div style="font-size:32px;font-weight:700;color:#1C1C1E;">{games_analyzed}</div>
          <div style="font-size:13px;color:#8E8E93;">Games Analyzed</div>
          {games_delta_html}
        </div>
        """, unsafe_allow_html=True)

    if st.button("View Detailed Stats", use_container_width=True):
        st.session_state["nav_target"] = "📚 Library"
        st.rerun()

    section_title("Settings")

    st.markdown("""
    <div class="nm-card" style="padding:0;">
      <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 20px;">
        <div style="display:flex;align-items:center;gap:10px;font-size:15px;font-weight:500;color:#34C759;">
          ⚙️ App Settings
        </div>
        <span style="color:#C7C7CC;">›</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:15px;font-weight:500;color:#34C759;margin:4px 0 8px;">🏆 Change Sport</div>', unsafe_allow_html=True)
    _sport_options = ["🏓 Pickleball", "🎾 Tennis", "🥎 Padel"]
    _sport_values = ["pickleball", "tennis", "padel"]
    sport_choice = st.radio(
        "Change Sport",
        _sport_options,
        index=_sport_values.index(st.session_state["sport"]) if st.session_state["sport"] in _sport_values else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="sport_radio_me"
    )
    st.session_state["sport"] = _sport_values[_sport_options.index(sport_choice)]

    st.markdown(f"<div style='font-size:13px;color:#8E8E93;margin:16px 0 6px;'>{current_user.email}</div>", unsafe_allow_html=True)
    with st.container(key="settings_row_btn"):
        if st.button("⏻  Se déconnecter", use_container_width=True):
            logout()
            st.rerun()

elif page == "📚 Library":
    exec(open(ROOT / "src/streamlit_app/1_Library.py", encoding="utf-8").read())

elif page == "⬆️ Upload":
    exec(open(ROOT / "src/streamlit_app/2_Upload.py", encoding="utf-8").read())

elif page == "📊 Dashboard":
    exec(open(ROOT / "src/streamlit_app/3_Dashboard.py", encoding="utf-8").read())

elif page == "🧠 AI Analysis":
    exec(open(ROOT / "src/streamlit_app/4_AI_Analysis.py", encoding="utf-8").read())

elif page == "📈 Patterns":
    exec(open(ROOT / "src/streamlit_app/5_Patterns.py", encoding="utf-8").read())

elif page == "📋 Training Plan":
    exec(open(ROOT / "src/streamlit_app/6_Training_Plan.py", encoding="utf-8").read())
