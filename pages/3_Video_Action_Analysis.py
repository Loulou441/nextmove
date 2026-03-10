import streamlit as st
import pandas as pd
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Chargement de la clé API
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Configuration des chemins
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
VIDEO_DIR = DATA_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# Ajout de la racine au path pour importer les modules
sys.path.append(str(ROOT))
from src.viz import create_tactical_pitch
from agentfootball.agent_recommendation_football import FootballCoachAI

st.set_page_config(page_title="Video Action Analysis", page_icon="🎬", layout="wide")

@st.cache_data
def load_matches():
    return pd.read_csv(DATA_DIR / "demo_matches.csv")

st.title("🎬 Analyse d’action via vidéo (NextMove POC)")

st.write(
    "Uploadez un clip vidéo. Notre pipeline simulera l'extraction par Computer Vision, "
    "et notre Agent IA générera une analyse tactique et des recommandations."
)

matches = load_matches()

# --- 1) SELECTION DU MATCH ---
st.subheader("1) Associer le clip à un match")
match_label = matches.apply(
    lambda r: f"{r['home_team']} {r['home_score']} - {r['away_score']} {r['away_team']} | {r['date']}",
    axis=1
)
selected = st.selectbox("Sélectionnez le match concerné", match_label)

st.divider()

# --- 2) UPLOAD ---
st.subheader("2) Uploader un clip vidéo")
uploaded = st.file_uploader("Clip vidéo amateur (mp4, mov)", type=["mp4", "mov", "m4v"])

if uploaded is not None:
    # Sauvegarde locale
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"video_poc_{timestamp}_{uploaded.name}".replace(" ", "_")
    saved_path = VIDEO_DIR / filename
    with open(saved_path, "wb") as f:
        f.write(uploaded.getbuffer())
    
    st.video(uploaded)

st.divider()

# --- 3) ANNOTATION (Simulation des données Vision) ---
st.subheader("3) Correction / Validation des données extraites")
st.info("Dans la version finale, ces champs seront remplis automatiquement par YOLOv8. Pour le POC, vous pouvez les ajuster.")

colA, colB, colC = st.columns(3)
with colA:
    minute = st.number_input("Minute de l'action", min_value=0, max_value=130, value=24)
with colB:
    player = st.text_input("Joueur ciblé", value="Lucas Martin")
with colC:
    event_type = st.selectbox("Événement détecté", ["Perte de balle", "Tir non cadré", "Passe décisive"])

st.write("**Localisation détectée (X/Y)**")
colX, colY = st.columns(2)
with colX:
    x = st.slider("Position X (0=Défense, 100=Attaque)", 0, 100, 72)
with colY:
    y = st.slider("Position Y (Vertical)", 0, 100, 45)

st.divider()

# --- 4) ANALYSE IA (Le cerveau) ---
if st.button("🚀 Lancer l’analyse NextMove IA", use_container_width=True, type="primary"):
    
    if not api_key:
        st.error("⚠️ Clé GROQ_API_KEY manquante dans le fichier .env !")
        st.stop()

    # Effet visuel du pipeline de traitement
    with st.status("Traitement du pipeline...", expanded=True) as status:
        st.write("🔍 Analyse vidéo et tracking des entités...")
        time.sleep(1)
        st.write("📐 Calcul des distances et extraction des KPIs...")
        time.sleep(1)
        status.update(label="Données visuelles extraites ! Génération du rapport IA...", state="complete", expanded=False)

    # 4.1 Préparation des données pour l'IA (On modifie le JSON d'Ayoub avec tes inputs)
    with open(ROOT / 'agentfootball/example_entry.json', 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    
    # On injecte les données saisies manuellement pour rendre la démo interactive
    match_data["joueur_analyse"]["nom"] = player
    match_data["donnees_sequences"][0]["timestamp_debut"] = f"{minute}:00"
    match_data["donnees_sequences"][0]["evenement_cle"] = event_type
    match_data["donnees_sequences"][0]["metriques_video"]["coordonnees_ballon"] = {"x": x, "y": y}

    # 4.2 Appel à l'IA
    try:
        with open(ROOT / 'agentfootball/context_football.txt', 'r', encoding='utf-8') as f:
            context = f.read()
        with open(ROOT / 'agentfootball/user_prompt_football.txt', 'r', encoding='utf-8') as f:
            prompt = f.read()

        user_prompt = f"{prompt}\nVoici les données du match : {match_data}"
        coach = FootballCoachAI(api_key, context, user_prompt)
        
        with st.spinner("Le SmartCoach rédige ses recommandations..."):
            recommandations = coach.generate_recommendations(match_data)
            
        st.success("Analyse terminée avec succès !")

        # 4.3 AFFICHAGE DES RÉSULTATS
        res_col1, res_col2 = st.columns([1, 1])

        with res_col1:
            st.markdown("### 🧠 Recommandations du Coach")
            for rec in recommandations.get("recommandations_coach", []):
                with st.container(border=True):
                    st.subheader(f"⏱ {rec['timestamp']} - {rec['titre']}")
                    c = rec["contenu"]
                    st.markdown(f"**📝 Constat :** {c['constat']}")
                    st.markdown(f"**🧠 Analyse :** {c['analyse']}")
                    st.success(f"**💡 Action :** {c['action_corrective']}")
                    if c.get("pro_tip"):
                        st.info(f"**🌟 Pro-Tip :** {c['pro_tip']}")

        with res_col2:
            st.markdown("### 📍 Modélisation 2D")
            # Appel à ta fonction de visualisation existante
            pitch_fig = create_tactical_pitch(x, y, player, event_type, phase="Analyse IA")
            st.plotly_chart(pitch_fig, use_container_width=True)

    except Exception as e:
        st.error(f"Une erreur s'est produite avec l'IA : {e}")