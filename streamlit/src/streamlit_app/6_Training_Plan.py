import streamlit as st
import json, os, time
from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title
from src.config import PROMPT_PATHS
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.training_plan_service import save_training_plan, get_user_training_plans

set_ios_design()
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

current_user = get_current_user()

page_header("Training Plan", "Your personalized weekly program")

# ── Sport selector ───────────────────────────────────────────────────
section_title("Select Sport")
_sport_options = ["🏓 Pickleball", "🎾 Tennis", "🥎 Padel"]
_sport_values = ["pickleball", "tennis", "padel"]
_file_suffixes = {"pickleball": "pickelball", "tennis": "tennis", "padel": "padel"}
default_sport_index = _sport_values.index(st.session_state.get("sport", "pickleball")) if st.session_state.get("sport", "pickleball") in _sport_values else 0
sport = st.radio("Sport", _sport_options, index=default_sport_index, horizontal=True, label_visibility="collapsed", key="sport_radio_training")
st.session_state["sport"] = _sport_values[_sport_options.index(sport)]
sport_value = st.session_state["sport"]
file_suffix = _file_suffixes[sport_value]
sport_badge = sport

st.markdown("<hr>", unsafe_allow_html=True)

# ── Player info ──────────────────────────────────────────────────────
try:
    with open(PROMPT_PATHS[sport_value] / "example_entry.json", encoding="utf-8") as f:
        match_data = json.load(f)
    joueur = match_data["joueur_analyse"]
except FileNotFoundError:
    match_data = {"joueur_analyse": {"nom": "Player", "position_predilection": "All-round"}, "donnees_sequences": []}
    joueur = match_data["joueur_analyse"]

player_position = joueur.get("position_predilection") or joueur.get("poste") or "All-round"

st.markdown(f"""
<div class="nm-card" style="display:flex;align-items:center;gap:16px;">
  <div style="width:48px;height:48px;background:#34C759;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">👤</div>
  <div>
    <div style="font-size:17px;font-weight:600;color:#1C1C1E;">{current_user.email}</div>
    <div style="font-size:14px;color:#8E8E93;">{player_position}</div>
  </div>
  <div style="margin-left:auto;">
    <span class="sport-badge">{sport_badge}</span>
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
            _demo_content = {
                "pickleball": [
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
                ],
                "tennis": [
                    {
                        "timestamp": "18:40",
                        "titre": "Service Consistency Under Pressure",
                        "contenu": {
                            "constat": "Double fault on break point, ball toss drifted backward under pressure.",
                            "analyse": "Service rhythm changes when the stakes rise, reducing the safety margin above the net.",
                            "action_corrective": "Practice 30 ball tosses without hitting, aiming for the exact same fixed point every time, before reintegrating the full swing.",
                            "pro_tip": "Novak Djokovic repeats an almost identical service ritual on every point, which stabilizes his toss even under pressure."
                        }
                    },
                    {
                        "timestamp": "31:15",
                        "titre": "Patience in Baseline Rallies",
                        "contenu": {
                            "constat": "Unforced error after a risky down-the-line acceleration during a neutral rally.",
                            "analyse": "The point was ended prematurely instead of being built patiently, taking on unnecessary risk.",
                            "action_corrective": "Directed rally drill: require at least three cross-court shots before any change of direction is allowed.",
                            "pro_tip": None
                        }
                    }
                ],
                "padel": [
                    {
                        "timestamp": "14:20",
                        "titre": "Net Positioning Discipline",
                        "contenu": {
                            "constat": "Direct fault at the net after moving in too early.",
                            "analyse": "Court positioning too aggressive against a lobbing opponent pair.",
                            "action_corrective": "Net approach drill: only move up after your partner's shot has crossed the net with a safe trajectory.",
                            "pro_tip": "Juan Lebrón always confirms his partner's shot quality before committing to the net."
                        }
                    },
                    {
                        "timestamp": "27:05",
                        "titre": "Off-the-Glass Anticipation",
                        "contenu": {
                            "constat": "Missed glass exit due to poor bounce anticipation.",
                            "analyse": "Late reaction to ball height and speed after the glass rebound.",
                            "action_corrective": "Glass exit drill: repeat controlled feeds off the back glass, focusing on early split-step and racket preparation.",
                            "pro_tip": "Alejandra Salazar tracks the ball off the glass with small adjustment steps, never standing flat-footed."
                        }
                    }
                ]
            }
            recommandations = {"recommandations_coach": _demo_content[sport_value]}
        else:
            try:
                if sport_value == "tennis":
                    from src.agents.agenttennis.agent_recommendation_tennis import TennisCoachAI as CoachClass
                elif sport_value == "padel":
                    from src.agents.agentpadel.agent_recommendation_padel import PadelCoachAI as CoachClass
                else:
                    from src.agents.agentpickelball.agent_recommendation_pickelball import PickelballCoachAI as CoachClass

                with open(PROMPT_PATHS[sport_value] / f"context_{file_suffix}.txt", encoding="utf-8") as f:  context = f.read()
                with open(PROMPT_PATHS[sport_value] / f"user_prompt_{file_suffix}.txt", encoding="utf-8") as f: prompt = f.read()
                user_prompt = f"{prompt}\nVoici l'intégralité des données du match : {match_data}"
                coach = CoachClass(context, user_prompt)
                recommandations = coach.generate_recommendations(match_data)
            except Exception as e:
                st.error(f"AI Error: {e}")
                st.stop()

    # ── Persist to DB, linked to the user and sport ─────────────────────
    with get_db_session() as db:
        save_training_plan(db, current_user.id, sport_value, recommandations)

    st.success("✅ Program generated and saved!")

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

# ── History of past plans for this sport ──────────────────────────────
with get_db_session() as db:
    past_plans = get_user_training_plans(db, current_user.id, sport=sport_value)
    for p in past_plans:
        db.expunge(p)

if past_plans:
    st.markdown("<hr>", unsafe_allow_html=True)
    section_title(f"📜 Past {sport_badge} plans")
    for p in past_plans:
        date_str = p.created_at.strftime("%b %d, %Y %H:%M") if p.created_at else ""
        recs = p.content.get("recommandations_coach", []) if p.content else []
        titles = ", ".join(r.get("titre", "") for r in recs) if recs else "Plan"
        with st.expander(f"{date_str} — {titles}"):
            for r in recs:
                st.write(f"**{r.get('titre')}** — {r.get('contenu', {}).get('analyse', '')}")