import os
import sys
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

st.set_page_config(
    page_title="NextMove",
    page_icon="🏓",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.design import set_ios_design, section_title, page_header

set_ios_design()

# ── Shared session state defaults ────────────────────────────────────
st.session_state.setdefault("sport", "pickleball")
st.session_state.setdefault("current_game_id", None)

# Apply any pending navigation request BEFORE the radio widget is instantiated
# (session_state for a widget's key can't be set after that widget has rendered).
if "nav_target" in st.session_state:
    st.session_state["nav_radio"] = st.session_state.pop("nav_target")

# ── Sidebar navigation ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 8px 0 20px;">
      <div style="font-size:22px;font-weight:700;color:#1C1C1E;">NextMove</div>
      <div style="font-size:13px;color:#8E8E93;">Smart Coach AI</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["👤  Me", "📚  Library", "⬆️  Upload", "📊  Dashboard", "🧠  AI Analysis", "📈  Patterns", "📋  Training Plan"],
        label_visibility="collapsed",
        key="nav_radio"
    )

# ── Route pages ──────────────────────────────────────────────────────
if page == "👤  Me":
    page_header("Me")

    _sport_labels = {"pickleball": "🏓 Pickleball", "football": "⚽ Football", "padel": "🎾 Padel"}
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

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="nm-card">
          <div style="font-size:22px;margin-bottom:4px;">⭐</div>
          <div style="font-size:32px;font-weight:700;color:#1C1C1E;">4.2</div>
          <div style="font-size:13px;color:#8E8E93;">Average Rating</div>
          <div style="font-size:12px;color:#34C759;margin-top:4px;">+0.3</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="nm-card">
          <div style="font-size:22px;margin-bottom:4px;">🎬</div>
          <div style="font-size:32px;font-weight:700;color:#1C1C1E;">3</div>
          <div style="font-size:13px;color:#8E8E93;">Games Analyzed</div>
          <div style="font-size:12px;color:#34C759;margin-top:4px;">+1</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("View Detailed Stats", use_container_width=True):
        st.session_state["nav_target"] = "📚  Library"
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
    _sport_options = ["🏓 Pickleball", "⚽ Football", "🎾 Padel"]
    _sport_values = ["pickleball", "football", "padel"]
    sport_choice = st.radio(
        "Change Sport",
        _sport_options,
        index=_sport_values.index(st.session_state["sport"]) if st.session_state["sport"] in _sport_values else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="sport_radio_me"
    )
    st.session_state["sport"] = _sport_values[_sport_options.index(sport_choice)]

elif page == "📚  Library":
    exec(open(ROOT / "src/streamlit_app/1_Library.py", encoding="utf-8").read())

elif page == "⬆️  Upload":
    exec(open(ROOT / "src/streamlit_app/2_Upload.py", encoding="utf-8").read())

elif page == "📊  Dashboard":
    exec(open(ROOT / "src/streamlit_app/3_Dashboard.py", encoding="utf-8").read())

elif page == "🧠  AI Analysis":
    exec(open(ROOT / "src/streamlit_app/4_AI_Analysis.py", encoding="utf-8").read())

elif page == "📈  Patterns":
    exec(open(ROOT / "src/streamlit_app/5_Patterns.py", encoding="utf-8").read())

elif page == "📋  Training Plan":
    exec(open(ROOT / "src/streamlit_app/6_Training_Plan.py", encoding="utf-8").read())
