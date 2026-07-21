import streamlit as st
import json, os, time
from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title

set_ios_design()
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

page_header("Training Plan", "Your personalized weekly program")

# ── Player info ──────────────────────────────────────────────────────
try:
    with open(ROOT / "agentfootball/example_entry.json") as f:
        match_data = json.load(f)
    joueur = match_data["joueur_analyse"]
except FileNotFoundError:
    match_data = {"joueur_analyse": {"nom": "Player", "poste": "All-round"}, "donnees_sequences": [], "stats_globales_match": {}}
    joueur = match_data["joueur_analyse"]

st.markdown(f"""
<div class="nm-card" style="display:flex;align-items:center;gap:16px;">
  <div style="width:48px;height:48px;background:#34C759;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">👤</div>
  <div>
    <div style="font-size:17px;font-weight:600;color:#1C1C1E;">{joueur['nom']}</div>
    <div style="font-size:14px;color:#8E8E93;">{joueur['poste']}</div>
  </div>
  <div style="margin-left:auto;">
    <span class="sport-badge">🏓 Pickleball</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Explainer ────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#EBF5FF;border-radius:14px;padding:16px 20px;margin-bottom:20px;">
  <div style="font-size:15px;font-weight:600;color:#007AFF;margin-bottom:6px;">💡 How it works</div>
  <div style="font-size:14px;color:#005CC5;line-height:1.6;">
    1. Our Computer Vision pipeline analyzed all critical sequences from your match.<br>
    2. The AI identified your main error patterns.<br>
    3. Click below to generate a personalized training program targeting your weak points.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Generate button ──────────────────────────────────────────────────
if st.button("🧠 Generate Weekly Training Plan", type="primary", use_container_width=True):

    demo_mode = not api_key

    with st.spinner("SmartCoach is building your program..."):
        time.sleep(1.5)

        if demo_mode:
            recommandations = {
                "recommandations_coach": [
                    {
                        "timestamp": "24:00",
                        "titre": "Third Shot Drop",
                        "contenu": {
                            "constat": "Third shot was consistently too hard, giving opponents easy volleys.",
                            "analyse": "Grip pressure too high at contact. Body weight not shifting forward properly.",
                            "action_corrective": "Practice 20 third shot drops daily from the baseline. Focus on soft hands and low trajectory over the net.",
                            "pro_tip": "Watch Anna Leigh Waters — notice how she relaxes her grip before contact on every third shot."
                        }
                    },
                    {
                        "timestamp": "38:00",
                        "titre": "Dinking Consistency",
                        "contenu": {
                            "constat": "Dink exchanges broken too early with aggressive shots.",
                            "analyse": "Patience threshold too low in kitchen rallies. Attacking from below net height.",
                            "action_corrective": "Kitchen dinking drill: maintain 15+ shot rallies with partner before attempting any attack. Attack only above net height.",
                            "pro_tip": "Ben Johns never rushes the dink — he waits for the ball to rise above net tape before any attack."
                        }
                    }
                ]
            }
        else:
            try:
                from src.agents.agentfootball.agent_recommendation_football import FootballCoachAI
                with open(ROOT / "agentfootball/context_football.txt") as f:  context = f.read()
                with open(ROOT / "agentfootball/user_prompt_football.txt") as f: prompt = f.read()
                user_prompt = f"{prompt}\nVoici l'intégralité des données du match : {match_data}"
                coach = FootballCoachAI(api_key, context, user_prompt)
                recommandations = coach.generate_recommendations(match_data)
            except Exception as e:
                st.error(f"AI Error: {e}")
                st.stop()

    st.success("✅ Program generated!")

    # ── Training cards ─────────────────────────────────────────────────
    section_title("🎯 Priority Workshops")
    recs = recommandations.get("recommandations_coach", [])

    for i, rec in enumerate(recs):
        c = rec["contenu"]
        st.markdown(f"""
        <div class="nm-card">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
            <div style="width:36px;height:36px;background:#34C759;border-radius:10px;display:flex;align-items:center;
                        justify-content:center;color:white;font-size:16px;font-weight:700;">{i+1}</div>
            <div>
              <div style="font-size:16px;font-weight:600;color:#1C1C1E;">Workshop {i+1}: {rec['titre']}</div>
              <div style="font-size:13px;color:#8E8E93;">Seen at {rec['timestamp']}</div>
            </div>
          </div>
          <div style="font-size:14px;color:#3C3C43;margin-bottom:10px;line-height:1.5;">{c['analyse']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="nm-card-green" style="margin-top:-4px;margin-bottom:12px;">
          <div style="font-size:12px;font-weight:600;color:#1A7F3C;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:4px;">🏋️ Exercise</div>
          <div style="font-size:14px;color:#1A7F3C;">{c['action_corrective']}</div>
        </div>
        """, unsafe_allow_html=True)

        if c.get("pro_tip"):
            st.markdown(f"""
            <div style="background:#EBF5FF;border-radius:12px;padding:12px 16px;margin-bottom:16px;">
              <div style="font-size:12px;color:#007AFF;font-weight:600;margin-bottom:2px;">🌟 Inspiration</div>
              <div style="font-size:13px;color:#005CC5;font-style:italic;">{c['pro_tip']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📄 Export Program as PDF (Coming Soon)",
            data="NextMove Training Program",
            file_name="nextmove_training.pdf",
            disabled=True,
            use_container_width=True
        )
else:
    st.markdown("""
    <div class="nm-card" style="text-align:center;padding:40px 20px;">
      <div style="font-size:48px;margin-bottom:12px;">🏋️</div>
      <div style="font-size:17px;font-weight:600;color:#1C1C1E;margin-bottom:8px;">Ready to improve?</div>
      <div style="font-size:14px;color:#8E8E93;line-height:1.6;">
        Generate your personalized training plan based on your last game analysis.
      </div>
    </div>
    """, unsafe_allow_html=True)
