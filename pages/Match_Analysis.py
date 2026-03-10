import streamlit as st
import pandas as pd
import json
import os
import sys
import time
from pathlib import Path
import plotly.express as px
from dotenv import load_dotenv

# Ajout du path pour importer l'IA d'Ayoub
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from agentfootball.agent_recommendation_football import FootballCoachAI

# Chargement API
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
DATA_DIR = ROOT / "data"

st.set_page_config(page_title="Match Analysis | NextMove", page_icon="🎥", layout="wide")

@st.cache_data
def load_matches():
    return pd.read_csv(DATA_DIR / "demo_matches.csv")

@st.cache_data
def load_events():
    df = pd.read_csv(DATA_DIR / "demo_events.csv")
    df["type"] = df["type"].astype(str)
    df["phase"] = df["phase"].astype(str)
    return df

st.title("🎥 Analyse Séquentielle du Match")
st.markdown("Naviguez dans la timeline du match extraite par notre Computer Vision et demandez au SmartCoach d'analyser une action spécifique.")

matches = load_matches()
events = load_events()

# --- 1. SÉLECTION DU MATCH ---
match_label = matches.apply(
    lambda r: f"{r['home_team']} {r['home_score']} - {r['away_score']} {r['away_team']} | {r['date']}",
    axis=1
)
selected = st.selectbox("Sélectionnez un match", match_label)

selected_row = matches.loc[match_label == selected].iloc[0]
match_id = int(selected_row["match_id"])
match_events = events[events["match_id"] == match_id].copy().sort_values(["minute", "second"])

st.divider()

# --- 2. TIMELINE VISUELLE ---
st.subheader("⏱️ Timeline des événements clés")
match_events["t"] = match_events["minute"] + match_events["second"] / 60.0
match_events["label"] = match_events.apply(
    lambda r: f"{int(r['minute'])}:{int(r['second']):02d} • {r['team']} • {r['type']} • {r['player']}",
    axis=1
)

fig = px.scatter(
    match_events, x="t", y="type", 
    color="team",
    hover_data=["label", "phase", "description"],
    title="Détection automatique des actions (Simulation Vision)"
)
fig.update_layout(template="plotly_dark", xaxis_title="Minute du match", yaxis_title="Type d'action")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 3. ANALYSE IA SUR MESURE ---
st.subheader("🧠 Demander une analyse tactique à l'IA")

key_events = match_events[match_events["type"].str.upper().isin(["GOAL", "TURNOVER", "SHOT"])].copy()
if key_events.empty:
    st.warning("Aucun événement clé trouvé dans ce match.")
    st.stop()

selected_event_label = st.selectbox("Sélectionnez l'événement à envoyer au SmartCoach :", key_events["label"].tolist())
selected_event = key_events[key_events["label"] == selected_event_label].iloc[0].to_dict()

if st.button("🤖 Générer le rapport pour cette action", type="primary"):
    
    # On simule l'injection de cet événement précis dans le JSON d'Ayoub
    with open(ROOT / 'agentfootball/example_entry.json', 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    
    # On modifie les données pour qu'elles correspondent à l'action cliquée
    match_data["donnees_sequences"][0]["timestamp_debut"] = f"{int(selected_event['minute'])}:{int(selected_event['second']):02d}"
    match_data["donnees_sequences"][0]["evenement_cle"] = selected_event['type']
    match_data["donnees_sequences"][0]["contexte_tactique"] = selected_event['description']
    match_data["joueur_analyse"]["nom"] = selected_event['player']

    with st.spinner("Le SmartCoach visionne la séquence et rédige son analyse..."):
        time.sleep(1) # Petit effet de chargement
        
        with open(ROOT / 'agentfootball/context_football.txt', 'r', encoding='utf-8') as f:
            context = f.read()
        with open(ROOT / 'agentfootball/user_prompt_football.txt', 'r', encoding='utf-8') as f:
            prompt = f.read()

        user_prompt = f"{prompt}\nVoici les données du match : {match_data}"
        
        try:
            coach = FootballCoachAI(api_key, context, user_prompt)
            recommandations = coach.generate_recommendations(match_data)
            
            st.success("Analyse terminée !")
            
            # Affichage du rapport
            for rec in recommandations.get("recommandations_coach", []):
                with st.container(border=True):
                    c = rec["contenu"]
                    st.markdown(f"**📝 Constat :** {c['constat']}")
                    st.markdown(f"**🧠 Analyse :** {c['analyse']}")
                    st.success(f"**💡 Action Corrective :** {c['action_corrective']}")
                    if c.get("pro_tip"):
                        st.info(f"**🌟 Pro-Tip :** {c['pro_tip']}")
        except Exception as e:
            st.error(f"Erreur de communication avec l'IA : {e}")