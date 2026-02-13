import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import des fonctions moteur
from src.analysis_engine import analyze_key_event, generate_tactical_narrative
from src.viz import create_tactical_pitch

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
    "L’analyse est semi-automatique : la vidéo sert de support, l’utilisateur fournit le contexte."
)

matches = load_matches()
events = load_events()

# --- 1) SELECTION DU MATCH ---
st.subheader("1) Associer le clip à un match")
match_label = matches.apply(
    lambda r: f"{r['home_team']} {r['home_score']} - {r['away_score']} {r['away_team']} | {r['date']}",
    axis=1
)
selected = st.selectbox("Sélectionnez le match concerné", match_label)
selected_row = matches.loc[match_label == selected].iloc[0]
match_id = int(selected_row["match_id"])
match_events = events[events["match_id"] == match_id].copy()

st.divider()

# --- 2) UPLOAD ---
st.subheader("2) Uploader un clip vidéo")
uploaded = st.file_uploader("Clip vidéo (mp4, mov)", type=["mp4", "mov", "m4v"])

saved_path = None
if uploaded is not None:
    # Sauvegarde locale pour le POC
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"match_{match_id}_{timestamp}_{uploaded.name}".replace(" ", "_")
    saved_path = VIDEO_DIR / filename
    with open(saved_path, "wb") as f:
        f.write(uploaded.getbuffer())
    
    st.video(uploaded)

st.divider()

# --- 3) ANNOTATION ---
st.subheader("3) Annotation de l’action")
colA, colB, colC = st.columns(3)

with colA:
    minute = st.number_input("Minute", min_value=0, max_value=130, value=60)
    second = st.number_input("Seconde", min_value=0, max_value=59, value=0)
with colB:
    team = st.text_input("Équipe en action", value=str(selected_row["away_team"]))
    player = st.text_input("Nom du joueur impliqué", value="Joueur X")
with colC:
    event_type = st.selectbox("Type d’événement", ["GOAL", "SHOT", "TURNOVER"])
    phase = st.selectbox("Phase de jeu", ["transition", "build-up", "set-piece"])

st.write("**Localisation de l'événement (X/Y)**")
colX, colY = st.columns(2)
with colX:
    x = st.slider("Position X (0=Défense, 100=Attaque)", 0, 100, 85)
with colY:
    y = st.slider("Position Y (Vertical)", 0, 100, 40)

st.divider()

# --- 4) ANALYSE ---
run = st.button("🚀 Lancer l’analyse IA", use_container_width=True)

if run:
    # Création de l'objet de donnée
    event_row = {
        "match_id": match_id, "minute": int(minute), "second": int(second),
        "team": team, "player": player, "type": event_type,
        "x": float(x), "y": float(y), "phase": phase,
        "description": "Analyse manuelle sur clip vidéo"
    }

    # Appel du moteur d'analyse
    result = analyze_key_event(event_row, match_events)
    narrative = generate_tactical_narrative(result, event_row)

    st.success("Analyse générée avec succès !")

    # AFFICHAGE DES RÉSULTATS EN DEUX COLONNES
    res_col1, res_col2 = st.columns([1, 1])

    with res_col1:
        st.markdown("### 🧠 Diagnostic de l'IA")
        st.markdown(narrative)
        
        st.write("**Répartition des responsabilités :**")
        st.progress(result.individual / 100, text=f"Individuelle : {result.individual}%")
        st.progress(result.collective / 100, text=f"Collective : {result.collective}%")
        st.progress(result.tactical / 100, text=f"Tactique (Coach) : {result.tactical}%")
        
        st.info(f"Niveau de confiance de l'analyse : **{result.confidence}**")

    with res_col2:
        st.markdown("### 📍 Modélisation 2D")
        pitch_fig = create_tactical_pitch(event_row['x'], event_row['y'], event_row['player'], event_row['type'], event_row['phase'])
        st.plotly_chart(pitch_fig, use_container_width=True)

    st.divider()
    
    # Recommandations
    st.subheader("📋 Recommandations pour l'entraînement")
    recs = st.columns(len(result.recommendations))
    for i, rec in enumerate(result.recommendations):
        recs[i].warning(rec)