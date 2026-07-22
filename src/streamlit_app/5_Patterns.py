import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title
from src.patterns_engine import compute_match_patterns

set_ios_design()
page_header("Patterns", "Tactical trends & collective behaviour")

DATA_DIR = ROOT / "data"

@st.cache_data
def load_games():   return pd.read_csv(DATA_DIR / "demo_games.csv")

try:
    @st.cache_data
    def load_events(): 
        df = pd.read_csv(DATA_DIR / "demo_events.csv")
        df["type"]  = df["type"].astype(str)
        df["phase"] = df["phase"].astype(str)
        return df
    events = load_events()
    has_events = True
except FileNotFoundError:
    has_events = False

games = load_games()
game_options = games["title"].tolist()
current_id = st.session_state.get("current_game_id")
if current_id in games["game_id"].values:
    default_index = game_options.index(games[games["game_id"] == current_id].iloc[0]["title"])
else:
    default_index = 0

selected = st.selectbox("Select Game", game_options, index=default_index, label_visibility="collapsed", key="patterns_game_select")
st.session_state["current_game_id"] = int(games[games["title"] == selected].iloc[0]["game_id"])

if not has_events:
    st.info("📊 Demo mode — event data file not found. Using simulated patterns.")

    # Simulated summary
    patterns = {
        "total_events": 21,
        "total_winners": 9,
        "total_shots": 6,
        "total_errors": 6,
        "phase_distribution": {"Transition": 8, "Service": 4, "Kitchen": 9},
        "zone_distribution":  {"Zone du filet (Kitchen)": 10, "Zone de transition avant": 6, "Zone médiane": 2, "Zone de fond de court (service)": 3},
        "transition_risk_ratio": 0.38,
        "priority_level": "Moyenne",
        "insights": [
            "Volume élevé d'échanges dans la zone du filet (Kitchen).",
            "Nombre important d'erreurs non forcées potentiellement évitables.",
        ]
    }
else:
    game_row = games[games["title"] == selected].iloc[0]
    match_events = events[events["match_id"] == int(game_row["game_id"])].copy()
    patterns = compute_match_patterns(match_events)

# ── KPIs ─────────────────────────────────────────────────────────────
section_title("Volume")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Events tracked",  patterns["total_events"])
c2.metric("Winners",         patterns["total_winners"])
c3.metric("Shots",           patterns["total_shots"])
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
