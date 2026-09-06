import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.match_service import get_user_matches

set_ios_design()
page_header("Patterns", "Tactical trends & collective behaviour")

current_user = get_current_user()

with get_db_session() as db:
    all_matches = get_user_matches(db, current_user.id)
    for m in all_matches:
        db.expunge(m)

ready_matches = [m for m in all_matches if m.status == "ready" and m.patterns_summary]

if not ready_matches:
    st.markdown("""
    <div class="nm-card" style="text-align:center;padding:32px 20px;">
      <div style="font-size:32px;margin-bottom:8px;">📈</div>
      <div style="font-size:17px;font-weight:600;color:#1C1C1E;">No pattern data yet</div>
      <div style="font-size:14px;color:#8E8E93;margin-top:4px;">Analyze a match from the Library to see its patterns here.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Game selector ───────────────────────────────────────────────────
match_by_title = {m.title: m for m in ready_matches}
titles = list(match_by_title.keys())
current_id = st.session_state.get("current_game_id")
default_index = 0
for i, m in enumerate(ready_matches):
    if m.id == current_id:
        default_index = i
        break

selected = st.selectbox("Select Game", titles, index=default_index, label_visibility="collapsed", key="patterns_game_select")
match = match_by_title[selected]
st.session_state["current_game_id"] = match.id

patterns = match.patterns_summary

# ── KPIs ─────────────────────────────────────────────────────────────
section_title("Volume")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Events tracked", patterns["total_events"])
c2.metric("Winners", patterns["total_winners"])
c3.metric("Shots", patterns["total_shots"])
c4.metric("Unforced Errors", patterns["total_errors"])

st.markdown("<hr>", unsafe_allow_html=True)

# ── Charts ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

CHART_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#1C1C1E"),
    showlegend=False,
    margin=dict(l=10, r=10, t=30, b=10),
    height=280
)

with col1:
    section_title("Phase Distribution")
    phase_df = pd.DataFrame(list(patterns["phase_distribution"].items()), columns=["Phase", "Count"])
    fig = px.bar(phase_df, x="Phase", y="Count", color="Phase",
                 color_discrete_sequence=["#34C759", "#007AFF", "#FF9500", "#FF3B30"])
    fig.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    section_title("Danger Zones")
    zone_df = pd.DataFrame(list(patterns["zone_distribution"].items()), columns=["Zone", "Count"])
    fig2 = px.pie(zone_df, values="Count", names="Zone", hole=0.45,
                  color_discrete_sequence=["#007AFF", "#34C759", "#FF9500", "#FF3B30"])
    fig2.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Structural alerts ─────────────────────────────────────────────────
section_title("⚠️ Structural Alerts")

level = patterns["priority_level"]
if level == "Élevée":
    st.error(f"**Priority level: {level}**")
elif level == "Moyenne":
    st.warning(f"**Priority level: {level}**")
else:
    st.success(f"**Priority level: {level}**")

st.markdown('<div class="nm-card">', unsafe_allow_html=True)
for insight in patterns["insights"]:
    st.markdown(f"""
    <div class="insight-item">
      <div class="insight-dot" style="background:#FF9500;"></div>
      {insight}
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
