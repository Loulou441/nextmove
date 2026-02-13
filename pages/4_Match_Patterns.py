import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

from src.patterns_engine import compute_match_patterns


st.set_page_config(page_title="Match Patterns", page_icon="📈", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

@st.cache_data
def load_matches():
    return pd.read_csv(DATA_DIR / "demo_matches.csv")

@st.cache_data
def load_events():
    df = pd.read_csv(DATA_DIR / "demo_events.csv")
    df["type"] = df["type"].astype(str)
    df["phase"] = df["phase"].astype(str)
    return df

st.title("📈 Match Patterns Analysis")

matches = load_matches()
events = load_events()

match_label = matches.apply(
    lambda r: f"{r['home_team']} {r['home_score']} - {r['away_score']} {r['away_team']} | {r['date']} | {r['competition']}",
    axis=1
)

selected = st.selectbox("Match", match_label)

selected_row = matches.loc[match_label == selected].iloc[0]
match_id = int(selected_row["match_id"])

match_events = events[events["match_id"] == match_id].copy()

patterns = compute_match_patterns(match_events)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Événements", patterns["total_events"])
col2.metric("Buts", patterns["total_goals"])
col3.metric("Tirs", patterns["total_shots"])
col4.metric("Pertes", patterns["total_turnovers"])

st.divider()

st.subheader("Distribution par phase")

phase_df = pd.DataFrame(
    list(patterns["phase_distribution"].items()),
    columns=["Phase", "Count"]
)

fig_phase = px.bar(phase_df, x="Phase", y="Count", title="Répartition par phase")
st.plotly_chart(fig_phase, use_container_width=True)

st.subheader("Distribution par zone")

zone_df = pd.DataFrame(
    list(patterns["zone_distribution"].items()),
    columns=["Zone", "Count"]
)

fig_zone = px.bar(zone_df, x="Zone", y="Count", title="Répartition par zone")
st.plotly_chart(fig_zone, use_container_width=True)

st.divider()

st.subheader("Insights automatiques (POC)")

for insight in patterns["insights"]:
    st.write(f"• {insight}")

st.markdown(f"### Niveau de priorité : {patterns['priority_level']}")

st.caption(
    "Synthèse générée automatiquement à partir de règles heuristiques. "
    "Amélioration future : apprentissage supervisé et validation sur dataset étendu."
)
