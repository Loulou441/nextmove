import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

from src.analysis_engine import analyze_key_event


st.set_page_config(page_title="Video Action Analysis", page_icon="🎬", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
VIDEO_DIR = ROOT / "data" / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

@st.cache_data
def load_matches():
    return pd.read_csv(DATA_DIR / "demo_matches.csv")

@st.cache_data
def load_events():
    df = pd.read_csv(DATA_DIR / "demo_events.csv")
    df["type"] = df["type"].astype(str)
    df["phase"] = df["phase"].astype(str)
    return df

st.title("🎬 Analyse d’action via vidéo (POC)")

st.write(
    "Cette page permet d’uploader un clip, d’annoter l’action, puis de générer une analyse IA explicative. "
    "L’analyse est semi-automatique : la vidéo sert de support, l’utilisateur fournit le contexte minimal."
)

matches = load_matches()
events = load_events()

st.subheader("1) Associer le clip à un match")

match_label = matches.apply(
    lambda r: f"{r['home_team']} {r['home_score']} - {r['away_score']} {r['away_team']} | {r['date']} | {r['competition']}",
    axis=1
)
selected = st.selectbox("Match", match_label)

selected_row = matches.loc[match_label == selected].iloc[0]
match_id = int(selected_row["match_id"])
match_events = events[events["match_id"] == match_id].copy()
match_events = match_events.sort_values(["minute", "second"])

st.divider()

st.subheader("2) Uploader un clip vidéo")

uploaded = st.file_uploader("Clip vidéo (mp4, mov)", type=["mp4", "mov", "m4v"])

saved_path = None
if uploaded is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"match_{match_id}_{timestamp}_{uploaded.name}".replace(" ", "_")
    saved_path = VIDEO_DIR / filename

    with open(saved_path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.success("Clip uploadé et enregistré pour le POC.")
    st.video(uploaded)

st.divider()

st.subheader("3) Annotation de l’action")

colA, colB, colC = st.columns(3)

with colA:
    minute = st.number_input("Minute", min_value=0, max_value=130, value=60, step=1)
    second = st.number_input("Seconde", min_value=0, max_value=59, value=0, step=1)

with colB:
    team = st.text_input("Équipe (libre)", value=str(selected_row["away_team"]))
    player = st.text_input("Joueur (optionnel)", value="Unknown")

with colC:
    event_type = st.selectbox("Type d’événement", ["GOAL", "SHOT", "TURNOVER"])
    phase = st.selectbox("Phase de jeu", ["transition", "build-up", "set-piece"])

st.write("Localisation approximative sur le terrain (format StatsBomb-like : x 0→100, y 0→100)")
colX, colY = st.columns(2)
with colX:
    x = st.slider("x", min_value=0, max_value=100, value=85)
with colY:
    y = st.slider("y", min_value=0, max_value=100, value=40)

description = st.text_area(
    "Description libre (optionnel)",
    value="Action issue du clip vidéo, annotée pour analyse IA."
)

st.divider()

st.subheader("4) Lancer l’analyse IA")

run = st.button("Analyser l’action")

if run:
    event_row = {
        "match_id": match_id,
        "minute": int(minute),
        "second": int(second),
        "team": team,
        "player": player,
        "type": event_type,
        "x": float(x),
        "y": float(y),
        "phase": phase,
        "description": description
    }

    result = analyze_key_event(event_row, match_events)

    st.success("Analyse générée.")

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

    st.markdown("### Recommandations")
    for rec in result.recommendations:
        st.write(f"• {rec}")

    st.markdown("### Métadonnées de l’action (POC)")
    st.json(event_row)

    if saved_path is not None:
        st.caption(f"Fichier vidéo enregistré : {saved_path.name}")
    else:
        st.warning("Aucun fichier vidéo n’a été uploadé. L’analyse a été faite uniquement sur l’annotation.")
