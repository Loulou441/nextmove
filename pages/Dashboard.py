import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

@st.cache_data
def load_matches():
    return pd.read_csv(DATA_DIR / "demo_matches.csv")

@st.cache_data
def load_events():
    return pd.read_csv(DATA_DIR / "demo_events.csv")

st.title("📊 Dashboard")

matches = load_matches()
events = load_events()

st.subheader("Sélection du match")
match_label = matches.apply(
    lambda r: f"{r['home_team']} {r['home_score']} - {r['away_score']} {r['away_team']} | {r['date']} | {r['competition']}",
    axis=1
)
selected = st.selectbox("Match", match_label)

selected_row = matches.loc[match_label == selected].iloc[0]
match_id = int(selected_row["match_id"])

match_events = events[events["match_id"] == match_id].copy()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Score", f"{selected_row['home_score']} - {selected_row['away_score']}")
with col2:
    st.metric("Événements", len(match_events))
with col3:
    goals = (match_events["type"] == "GOAL").sum()
    st.metric("Buts", int(goals))

st.divider()

st.subheader("Événements du match (demo)")
st.dataframe(match_events.sort_values(["minute", "second"]), use_container_width=True)

st.divider()

st.subheader("3 insights (demo)")
st.write("1) Les transitions semblent être une source majeure de danger.")
st.write("2) Les pertes de balle au milieu créent des situations à risque.")
st.write("3) Les tirs adverses viennent souvent après récupération haute.")
