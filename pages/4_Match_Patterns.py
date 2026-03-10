import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

# Import du moteur existant dans ton dossier src/
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from src.patterns_engine import compute_match_patterns

st.set_page_config(page_title="Match Patterns | NextMove", page_icon="📈", layout="wide")

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

st.title("📈 Tendances Tactiques & Patterns")
st.markdown("Vue macroscopique du match : analyse des comportements collectifs basés sur l'agrégation de milliers de coordonnées (X,Y).")

matches = load_matches()
events = load_events()

match_label = matches.apply(
    lambda r: f"{r['home_team']} {r['home_score']} - {r['away_score']} {r['away_team']} | {r['date']}",
    axis=1
)

selected = st.selectbox("Sélectionnez un match", match_label)

selected_row = matches.loc[match_label == selected].iloc[0]
match_id = int(selected_row["match_id"])
match_events = events[events["match_id"] == match_id].copy()

# Calcul via ton moteur Python (src/patterns_engine.py)
patterns = compute_match_patterns(match_events)

# --- 1. METRIQUES D'ÉQUIPE ---
st.subheader("Volume de jeu")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Événements traqués", patterns["total_events"])
col2.metric("Buts", patterns["total_goals"])
col3.metric("Tirs", patterns["total_shots"])
col4.metric("Pertes de balle", patterns["total_turnovers"])

st.divider()

# --- 2. GRAPHIQUES ---
col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    st.subheader("Distribution par phase de jeu")
    phase_df = pd.DataFrame(list(patterns["phase_distribution"].items()), columns=["Phase", "Count"])
    fig_phase = px.bar(phase_df, x="Phase", y="Count", color="Phase", title="Phases les plus actives")
    fig_phase.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_phase, use_container_width=True)

with col_graph2:
    st.subheader("Zones de danger (Pitch Grid)")
    zone_df = pd.DataFrame(list(patterns["zone_distribution"].items()), columns=["Zone", "Count"])
    fig_zone = px.pie(zone_df, values="Count", names="Zone", hole=0.4, title="Où se passe l'action ?")
    fig_zone.update_layout(template="plotly_dark")
    st.plotly_chart(fig_zone, use_container_width=True)

st.divider()

# --- 3. INSIGHTS MACRO ---
st.subheader("⚠️ Alertes Structurelles (Insights Automatiques)")

if patterns["priority_level"] == "Élevée":
    st.error(f"**Niveau de priorité d'intervention : {patterns['priority_level']}**")
elif patterns["priority_level"] == "Moyenne":
    st.warning(f"**Niveau de priorité d'intervention : {patterns['priority_level']}**")
else:
    st.success(f"**Niveau de priorité d'intervention : {patterns['priority_level']}**")

for insight in patterns["insights"]:
    st.info(f"🔍 {insight}")

st.caption("Dans la version finale, ces macro-tendances seront croisées avec les LLMs pour générer des recommandations à l'échelle de l'équipe entière.")