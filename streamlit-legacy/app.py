import os
import streamlit as st
from src.design import set_pro_design


st.set_page_config(
    page_title="TactiCore",
    page_icon="⚽",
    layout="wide"
)

# Affichage du logo sécurisé et sans warning
logo_path = "assets/logo.png"
if os.path.exists(logo_path):
    try:
        # On utilise width="stretch" au lieu de use_container_width=True
        st.sidebar.image(logo_path, width="stretch")
    except Exception:
        st.sidebar.warning("⚠️ L'image logo.png est corrompue.")

st.sidebar.markdown("---") # Petite ligne de séparation

set_pro_design()

st.title("TactiCore")
st.write("Bienvenue. Utilise le menu à gauche pour naviguer.")

st.info("Si tu vois ce message, Streamlit fonctionne. Prochaine étape : Dashboard avec données.")
