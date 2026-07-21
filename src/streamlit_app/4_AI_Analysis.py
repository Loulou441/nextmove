import streamlit as st
import pandas as pd
import json, os, time
from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title
from src.viz import create_tactical_pitch

set_ios_design()
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

page_header("AI Analysis", "Get instant coaching insights")

# ── Sport selector ──────────────────────────────────────────────────
section_title("Select Sport")
sport = st.radio("", ["🏓 Pickleball", "⚽ Football"], horizontal=True, label_visibility="collapsed")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Action input ─────────────────────────────────────────────────────
section_title("Action Details")

col1, col2 = st.columns(2)
with col1:
    minute = st.number_input("Minute", min_value=0, max_value=130, value=24)
    player = st.text_input("Player", value="Lucas Martin" if "Football" in sport else "Player 1")
with col2:
    if "Football" in sport:
        event_type = st.selectbox("Event", ["Perte de balle", "Tir non cadré", "Passe décisive"])
    else:
        event_type = st.selectbox("Event", ["Rally Error", "Winner Shot", "Service Fault", "Poach"])

col_x, col_y = st.columns(2)
with col_x:
    x = st.slider("Position X", 0, 100, 72)
with col_y:
    y = st.slider("Position Y", 0, 100, 45)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Run analysis ─────────────────────────────────────────────────────
if st.button("🚀 Generate AI Coaching Report", use_container_width=True, type="primary"):

    if not api_key:
        st.warning("⚠️ No GROQ_API_KEY found. Showing demo output.")
        demo_mode = True
    else:
        demo_mode = False

    with st.status("Processing...", expanded=True) as status:
        st.write("🎯 Detecting key elements...")
        time.sleep(0.8)
        st.write("📐 Calculating KPIs and distances...")
        time.sleep(0.8)
        status.update(label="Generating AI report...", state="complete", expanded=False)

    if demo_mode:
        # Demo output matching iOS app style
        recommandations = {
            "recommandations_coach": [
                {
                    "timestamp": f"{minute}:00",
                    "titre": "Positioning Error",
                    "contenu": {
                        "constat": f"Error detected at minute {minute} — {event_type} in zone x={x}.",
                        "analyse": "Body orientation was closed, preventing vision of teammate's run. The position relative to the net was too passive.",
                        "action_corrective": "Scan the court every 2 seconds before receiving. Work on open body positioning drills with a partner.",
                        "pro_tip": "Observe how Ben Johns positions his feet before each kitchen exchange — always sideways, never flat-footed."
                    }
                }
            ]
        }
    else:
        try:
            from src.agents.agentfootball.agent_recommendation_football import FootballCoachAI
            with open(ROOT / "agentfootball/example_entry.json", "r") as f:
                match_data = json.load(f)
            match_data["joueur_analyse"]["nom"] = player
            match_data["donnees_sequences"][0]["timestamp_debut"] = f"{minute}:00"
            match_data["donnees_sequences"][0]["evenement_cle"] = event_type
            match_data["donnees_sequences"][0]["metriques_video"]["coordonnees_ballon"] = {"x": x, "y": y}

            with open(ROOT / "agentfootball/context_football.txt") as f: context = f.read()
            with open(ROOT / "agentfootball/user_prompt_football.txt") as f: prompt = f.read()
            user_prompt = f"{prompt}\nVoici les données du match : {match_data}"

            coach = FootballCoachAI(api_key, context, user_prompt)
            with st.spinner("SmartCoach is writing recommendations..."):
                recommandations = coach.generate_recommendations(match_data)
        except Exception as e:
            st.error(f"AI Error: {e}")
            st.stop()

    # ── Results display ───────────────────────────────────────────────
    col_rec, col_pitch = st.columns([1, 1])

    with col_rec:
        section_title("🧠 Coach Recommendations")
        for rec in recommandations.get("recommandations_coach", []):
            c = rec["contenu"]
            st.markdown(f"""
            <div class="nm-card">
              <div style="font-size:13px;color:#8E8E93;margin-bottom:8px;">⏱ {rec['timestamp']} · {rec['titre']}</div>
              <div style="margin-bottom:10px;">
                <div style="font-size:12px;color:#8E8E93;font-weight:600;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:3px;">📝 Constat</div>
                <div style="font-size:14px;color:#1C1C1E;">{c['constat']}</div>
              </div>
              <div style="margin-bottom:10px;">
                <div style="font-size:12px;color:#8E8E93;font-weight:600;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:3px;">🧠 Analyse</div>
                <div style="font-size:14px;color:#1C1C1E;">{c['analyse']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="nm-card-green">
              <div style="font-size:12px;color:#34C759;font-weight:600;text-transform:uppercase;margin-bottom:3px;">💡 Action</div>
              <div style="font-size:14px;color:#1A7F3C;">{c['action_corrective']}</div>
            </div>
            """, unsafe_allow_html=True)

            if c.get("pro_tip"):
                st.markdown(f"""
                <div style="background:#EBF5FF;border-radius:12px;padding:14px 16px;margin-bottom:12px;">
                  <div style="font-size:12px;color:#007AFF;font-weight:600;margin-bottom:3px;">🌟 Pro-Tip</div>
                  <div style="font-size:13px;color:#005CC5;font-style:italic;">{c['pro_tip']}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_pitch:
        section_title("📍 Tactical View")
        pitch_fig = create_tactical_pitch(x, y, player, event_type, phase="AI Analysis")
        pitch_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans")
        )
        st.plotly_chart(pitch_fig, use_container_width=True)
