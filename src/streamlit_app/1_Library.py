import pandas as pd
import streamlit as st
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title, skill_bar, performance_ring, kpi_grid, strengths_focus
from src.config import DATA_DIR

set_ios_design()
page_header("Library", "Your analyzed games")

@st.cache_data
def load_games():
    return pd.read_csv(DATA_DIR / "demo_games.csv")

games = load_games()

# ── Game list ───────────────────────────────────────────────────────
for _, g in games.iterrows():
    status_html = (
        '<span class="status-badge status-ready">✓ Ready</span>'
        if g["status"] == "ready"
        else '<span class="status-badge status-pending">⏳ Pending</span>'
    )
    st.markdown(f"""
    <div class="game-card">
      <div class="game-card-header">
        <div>
          <div class="game-card-title">{g['title']}</div>
          <div style="display:flex;gap:8px;align-items:center;margin-top:4px;">
            <span class="sport-badge" style="font-size:12px;padding:2px 8px;">🏓 {g['sport']}</span>
            <span class="game-card-date">{g['date']} · {g['duration']}</span>
          </div>
        </div>
        {status_html}
      </div>
    </div>
    """, unsafe_allow_html=True)

    if g["status"] == "ready":
        col_r, col_ral, col_win = st.columns(3)
        col_r.metric("Rating", g["rating"])
        col_ral.metric("Rallies", int(g["rallies"]))
        col_win.metric("Winners", int(g["winners"]))

        if st.button(f"📊 Open Analysis — {g['title']}", key=f"open_{g['game_id']}", use_container_width=True, type="primary"):
            st.session_state["selected_game"] = g.to_dict()
            st.session_state["current_game_id"] = int(g["game_id"])
            st.session_state["nav_target"] = "📊  Dashboard"
            st.rerun()
    else:
        if st.button(f"🔍 Analyze Game — {g['title']}", key=f"analyze_{g['game_id']}", use_container_width=True):
            with st.spinner("Analyzing..."):
                import time; time.sleep(2)
            st.success("Analysis complete!")

    st.markdown("<hr>", unsafe_allow_html=True)
