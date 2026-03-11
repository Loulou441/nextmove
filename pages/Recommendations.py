import streamlit as st
import pandas as pd
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 1. Configuration de la page EN PREMIER
st.set_page_config(page_title="Recommandations | NextMove", page_icon="📋", layout="wide")

# 2. Ajout du path pour les imports locaux
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

# 3. Imports locaux
from agentfootball.agent_recommendation_football import FootballCoachAI
from src.design import set_pro_design

# 4. Application du CSS
set_pro_design()

# Chargement API
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

st.title("📋 Programme d'Entraînement Personnalisé")
st.markdown("Bilan complet du match et axes d'amélioration générés par le SmartCoach IA.")

# --- 1. SÉLECTION DU JOUEUR ---
col_info1, col_info2 = st.columns([2, 1])

with col_info1:
    st.info("💡 **Mode POC** : Ce rapport agrège toutes les séquences critiques détectées par la Vision lors du match pour construire un plan de travail sur mesure.")

# Chargement des données globales d'Ayoub (qui contient plusieurs séquences)
try:
    with open(ROOT / 'agentfootball/example_entry.json', 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    joueur = match_data["joueur_analyse"]
except FileNotFoundError:
    st.error("Fichier example_entry.json introuvable.")
    st.stop()

with col_info2:
    st.markdown(f"**👤 Joueur :** {joueur['nom']}")
    st.markdown(f"**👕 Poste :** {joueur['poste']}")
    st.markdown(f"**📅 Match ID :** {match_data['match_id']}")

st.divider()

# --- 2. GÉNÉRATION DU BILAN GLOBAL ---
if st.button("🧠 Générer le plan d'entraînement de la semaine", type="primary", use_container_width=True):
    
    if not api_key:
        st.error("⚠️ Clé GROQ_API_KEY manquante.")
        st.stop()

    with st.spinner("Le SmartCoach compile toutes les données du match et prépare votre programme..."):
        time.sleep(1.5) # Effet de calcul
        
        try:
            with open(ROOT / 'agentfootball/context_football.txt', 'r', encoding='utf-8') as f:
                context = f.read()
            with open(ROOT / 'agentfootball/user_prompt_football.txt', 'r', encoding='utf-8') as f:
                prompt = f.read()

            user_prompt = f"{prompt}\nVoici l'intégralité des données du match : {match_data}"
            
            coach = FootballCoachAI(api_key, context, user_prompt)
            recommandations = coach.generate_recommendations(match_data)
            
            st.success("Programme généré avec succès !")
            
            # --- 3. AFFICHAGE SOUS FORME DE "TO-DO LIST" ---
            st.markdown("### 🎯 Vos axes de travail prioritaires")
            
            recs = recommandations.get("recommandations_coach", [])
            
            # On divise l'affichage en colonnes pour faire des "Cartes d'exercices"
            cols = st.columns(len(recs) if len(recs) > 0 else 1)
            
            for index, rec in enumerate(recs):
                with cols[index % len(cols)]: # Répartit les cartes dans les colonnes
                    with st.container(border=True):
                        st.subheader(f"🛠️ Atelier {index + 1}")
                        st.markdown(f"**Objectif :** Corriger la {rec['titre'].lower()} (vue à la {rec['timestamp']})")
                        
                        c = rec["contenu"]
                        st.markdown(f"**Diagnostique :** {c['analyse']}")
                        
                        # Mise en avant de l'action
                        st.success(f"**🏋️ Exercice :** {c['action_corrective']}")
                        
                        if c.get("pro_tip"):
                            st.caption(f"🌟 **Inspiration :** {c['pro_tip']}")
            
            st.divider()
            
            # Bouton factice pour l'illusion SaaS (Téléchargement PDF)
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                st.download_button(
                    label="📄 Exporter ce programme en PDF (Bientôt disponible)",
                    data="Simulation PDF",
                    file_name="programme_nextmove.pdf",
                    disabled=True,
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")
else:
    # État vide avant de cliquer sur le bouton
    st.markdown("""
    #### Comment fonctionne cette page ?
    1. Notre pipeline **Computer Vision** a tourné sur l'intégralité du match.
    2. Il a isolé plusieurs séquences clés (ex: une perte de balle dangereuse, un tir non cadré).
    3. En cliquant sur le bouton ci-dessus, notre **Agent IA** va analyser l'ensemble de ces erreurs pour vous proposer un programme d'entraînement cohérent.
    """)