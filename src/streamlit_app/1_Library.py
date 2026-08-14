import streamlit as st
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.match_service import get_user_matches, mark_match_ready

set_ios_design()
page_header("Library", "Your analyzed games")

current_user = get_current_user()

_sport_icons = {"pickleball": "🏓", "football": "⚽", "padel": "🎾"}

with get_db_session() as db:
    matches = get_user_matches(db, current_user.id)
    # Détache les objets pour pouvoir les utiliser après la fermeture de la session
    for m in matches:
        db.expunge(m)

if not matches:
    st.markdown("""
    <div class="nm-card" style="text-align:center;padding:32px 20px;">
      <div style="font-size:32px;margin-bottom:8px;">📭</div>
      <div style="font-size:17px;font-weight:600;color:#1C1C1E;">No games yet</div>
      <div style="font-size:14px;color:#8E8E93;margin-top:4px;">Upload your first match to see it here.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⬆️ Go to Upload", use_container_width=True, type="primary"):
        st.session_state["nav_target"] = "⬆️  Upload"
        st.rerun()

# ── Game list ───────────────────────────────────────────────────────
for m in matches:
    status_html = (
        '<span class="status-badge status-ready">✓ Ready</span>'
        if m.status == "ready"
        else '<span class="status-badge status-pending">⏳ Pending</span>'
    )
    sport_icon = _sport_icons.get(m.sport, "🏓")
    date_str = m.match_date.strftime("%b %d, %Y") if m.match_date else ""

    st.markdown(f"""
    <div class="game-card">
      <div class="game-card-header">
        <div>
          <div class="game-card-title">{m.title}</div>
          <div style="display:flex;gap:8px;align-items:center;margin-top:4px;">
            <span class="sport-badge" style="font-size:12px;padding:2px 8px;">{sport_icon} {m.sport}</span>
            <span class="game-card-date">{date_str}</span>
          </div>
        </div>
        {status_html}
      </div>
    </div>
    """, unsafe_allow_html=True)

    if m.status == "ready":
        col_r, col_ral, col_win = st.columns(3)
        col_r.metric("Rating", m.rating)
        col_ral.metric("Rallies", m.rallies)
        col_win.metric("Winners", m.winners)

        if st.button(f"📊 Open Analysis — {m.title}", key=f"open_{m.id}", use_container_width=True, type="primary"):
            st.session_state["current_game_id"] = m.id
            st.session_state["nav_target"] = "📊  Dashboard"
            st.rerun()
    else:
        if st.button(f"🔍 Analyze Game — {m.title}", key=f"analyze_{m.id}", use_container_width=True):
            with st.spinner("Analyzing..."):
                with get_db_session() as db:
                    mark_match_ready(db, m.id)
            st.success("Analysis complete!")
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)