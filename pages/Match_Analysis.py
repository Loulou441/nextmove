import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

from src.analysis_engine import analyze_key_event


st.set_page_config(page_title="Match Analysis", page_icon="🎥", layout="wide")

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

st.title("🎥 Match Analysis")

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
match_events = match_events.sort_values(["minute", "second"])

st.subheader("Timeline des événements")

match_events["t"] = match_events["minute"] + match_events["second"] / 60.0
match_events["label"] = match_events.apply(
    lambda r: f"{int(r['minute'])}:{int(r['second']):02d} • {r['team']} • {r['type']} • {r['player']}",
    axis=1
)

fig = px.scatter(
    match_events,
    x="t",
    y="type",
    hover_data=["label", "phase", "description"],
    title="Timeline (demo)"
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Choisir une action clé à analyser")

key_events = match_events[match_events["type"].str.upper().isin(["GOAL", "TURNOVER", "SHOT"])].copy()
if key_events.empty:
    st.warning("Aucun événement clé trouvé dans ce match.")
    st.stop()

selected_event_label = st.selectbox("Événement", key_events["label"].tolist())
selected_event = key_events[key_events["label"] == selected_event_label].iloc[0].to_dict()

result = analyze_key_event(selected_event, match_events)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Responsabilité estimée")
    st.metric("Individuelle", f"{result.individual} %")
    st.metric("Collective", f"{result.collective} %")
    st.metric("Tactique", f"{result.tactical} %")
    st.caption(f"Niveau de confiance : {result.confidence}")

with col2:
    st.markdown("### Explication IA")
    st.write(result.explanation)

st.divider()

st.markdown("### Recommandations")
for rec in result.recommendations:
    st.write(f"• {rec}")

st.divider()

st.markdown("### Détails de l’événement sélectionné")
st.json(selected_event)
