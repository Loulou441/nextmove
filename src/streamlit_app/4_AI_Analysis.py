import streamlit as st
import json, os, time
from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title
from src.viz import create_tactical_pitch
from src.config import PROMPT_PATH_FOOTBALL, PROMPT_PATH_PADEL, PROMPT_PATH_PICKELBALL
from src.agents.agentmoderator.agent_moderator import Moderator
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.match_service import get_user_matches
from src.services.analysis_service import save_analysis, get_match_analyses

set_ios_design()
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

current_user = get_current_user()

with get_db_session() as db:
    all_matches = get_user_matches(db, current_user.id)
    for m in all_matches:
        db.expunge(m)

if not all_matches:
    page_header("AI Analysis")
    st.markdown("""
    <div class="nm-card" style="text-align:center;padding:32px 20px;">
      <div style="font-size:32px;margin-bottom:8px;">🧠</div>
      <div style="font-size:17px;font-weight:600;color:#1C1C1E;">No matches yet</div>
      <div style="font-size:14px;color:#8E8E93;margin-top:4px;">Upload a match first to generate a coaching report for it.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

page_header("AI Analysis", "Get instant coaching insights")

# ── Match selector (le rapport sera lié à ce match) ───────────────────
section_title("Select Match")
match_by_title = {m.title: m for m in all_matches}
titles = list(match_by_title.keys())
current_id = st.session_state.get("current_game_id")
default_index = 0
for i, m in enumerate(all_matches):
    if m.id == current_id:
        default_index = i
        break

selected_title = st.selectbox(
    "Match", titles, index=default_index,
    label_visibility="collapsed", key="ai_analysis_match_select"
)
match = match_by_title[selected_title]
st.session_state["current_game_id"] = match.id

sport = match.sport
_sport_labels = {"pickleball": "🏓 Pickleball", "football": "⚽ Football", "padel": "🎾 Padel"}
st.markdown(f'<span class="sport-badge">{_sport_labels.get(sport, sport)}</span>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Action input ─────────────────────────────────────────────────────
section_title("Action Details")

col1, col2 = st.columns(2)
with col1:
    minute = st.number_input("Minute", min_value=0, max_value=130, value=24)
    if sport == "football":
        default_player = "Lucas Martin"
    elif sport == "padel":
        default_player = "Marco Duran"
    else:
        default_player = "Player 1"
    player = st.text_input("Player", value=default_player)
with col2:
    if sport == "football":
        event_type = st.selectbox("Event", ["Perte de balle", "Tir non cadré", "Passe décisive"])
    elif sport == "padel":
        event_type = st.selectbox("Event", ["Faute directe au filet", "Sortie de vitre manquée", "Amortie gagnante", "Lob gagnant"])
    else:
        event_type = st.selectbox("Event", ["Rally Error", "Winner Shot", "Service Fault", "Poach"])

col_x, col_y = st.columns(2)
with col_x:
    x = st.slider("Position X", 0, 100, 72)
with col_y:
    y = st.slider("Position Y", 0, 100, 45)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Ask the AI coach ─────────────────────────────────────────────────
section_title("💬 Ask Your AI Coach (optional)")
coach_question = st.text_area(
    "Question for the coach",
    placeholder="e.g. Why do I keep losing the ball on my left side?",
    label_visibility="collapsed",
    key="coach_question",
)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Run analysis ─────────────────────────────────────────────────────
if st.button("🚀 Generate AI Coaching Report", use_container_width=True, type="primary"):

    if not api_key:
        st.warning("⚠️ No GROQ_API_KEY found. Showing demo output.")
        demo_mode = True
    else:
        demo_mode = False

    question = coach_question.strip()

    if question and not demo_mode:
        try:
            moderation = Moderator().moderate(question)
        except Exception as e:
            st.warning(f"⚠️ Could not verify your question ({e}). Ignoring it for this report.")
            moderation = {"is_prompt_injection": False}
            question = ""

        if moderation.get("is_prompt_injection"):
            st.error("🚫 Your question looks like it's trying to manipulate the AI coach and was blocked. Please rephrase it as a normal coaching question.")
            st.stop()

    with st.status("Processing...", expanded=True) as status:
        st.write("🎯 Detecting key elements...")
        time.sleep(0.8)
        st.write("📐 Calculating KPIs and distances...")
        time.sleep(0.8)
        status.update(label="Generating AI report...", state="complete", expanded=False)

    if demo_mode:
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
            if sport == "football":
                from src.agents.agentfootball.agent_recommendation_football import FootballCoachAI

                with open(PROMPT_PATH_FOOTBALL / "example_entry.json", "r", encoding="utf-8") as f:
                    match_data = json.load(f)
                match_data["joueur_analyse"]["nom"] = player
                match_data["donnees_sequences"][0]["timestamp_debut"] = f"{minute}:00"
                match_data["donnees_sequences"][0]["evenement_cle"] = event_type
                match_data["donnees_sequences"][0]["metriques_video"]["coordonnees_ballon"] = {"x": x, "y": y}

                with open(PROMPT_PATH_FOOTBALL / "context_football.txt", encoding="utf-8") as f: context = f.read()
                with open(PROMPT_PATH_FOOTBALL / "user_prompt_football.txt", encoding="utf-8") as f: prompt = f.read()
                user_prompt = f"{prompt}\nVoici les données du match : {match_data}"
                if question:
                    user_prompt += f"\n\nQuestion posée par le joueur : {question}"

                coach = FootballCoachAI(context, user_prompt)
            elif sport == "padel":
                from src.agents.agentpadel.agent_recommendation_padel import PadelCoachAI

                with open(PROMPT_PATH_PADEL / "example_entry.json", "r", encoding="utf-8") as f:
                    match_data = json.load(f)
                match_data["joueur_analyse"]["nom"] = player
                match_data["donnees_sequences"][0]["timestamp"] = f"{minute}:00"
                match_data["donnees_sequences"][0]["evenement_cle"] = event_type
                match_data["donnees_sequences"][0]["metriques_video"]["position_pieds"] = {"x": x, "y": y}

                with open(PROMPT_PATH_PADEL / "context_padel.txt", encoding="utf-8") as f: context = f.read()
                with open(PROMPT_PATH_PADEL / "user_prompt_padel.txt", encoding="utf-8") as f: prompt = f.read()
                user_prompt = f"{prompt}\nVoici les données du match : {match_data}"
                if question:
                    user_prompt += f"\n\nQuestion posée par le joueur : {question}"

                coach = PadelCoachAI(context, user_prompt)
            else:
                from src.agents.agentpickelball.agent_recommendation_pickelball import PickelballCoachAI

                with open(PROMPT_PATH_PICKELBALL / "example_entry.json", "r", encoding="utf-8") as f:
                    match_data = json.load(f)
                match_data["joueur_analyse"]["nom"] = player
                match_data["donnees_sequences"][0]["timestamp"] = f"{minute}:00"
                match_data["donnees_sequences"][0]["evenement_cle"] = event_type
                match_data["donnees_sequences"][0]["metriques_video"]["position_pieds"] = {"x": x, "y": y}

                with open(PROMPT_PATH_PICKELBALL / "context_pickelball.txt", encoding="utf-8") as f: context = f.read()
                with open(PROMPT_PATH_PICKELBALL / "user_prompt_pickelball.txt", encoding="utf-8") as f: prompt = f.read()
                user_prompt = f"{prompt}\nVoici les données du match : {match_data}"
                if question:
                    user_prompt += f"\n\nQuestion posée par le joueur : {question}"

                coach = PickelballCoachAI(context, user_prompt)

            with st.spinner("SmartCoach is writing recommendations..."):
                recommandations = coach.generate_recommendations(match_data)
        except Exception as e:
            st.error(f"AI Error: {e}")
            st.stop()

    # ── Persist to DB, linked to the selected match ────────────────────
    with get_db_session() as db:
        save_analysis(db, match.id, recommandations)

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

        st.success(f"✅ Report saved to \"{match.title}\"")

    with col_pitch:
        section_title("📍 Tactical View")
        pitch_fig = create_tactical_pitch(
            x, y, player, event_type, phase="AI Analysis", sport=sport
        )
        pitch_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans")
        )
        st.plotly_chart(pitch_fig, use_container_width=True)

# ── History of past reports for this match ────────────────────────────
with get_db_session() as db:
    past_analyses = get_match_analyses(db, match.id)
    for a in past_analyses:
        db.expunge(a)

if past_analyses:
    st.markdown("<hr>", unsafe_allow_html=True)
    section_title(f"📜 Past reports for \"{match.title}\"")
    for a in past_analyses:
        date_str = a.created_at.strftime("%b %d, %Y %H:%M") if a.created_at else ""
        with st.expander(f"{date_str} — {a.explanation[:60] if a.explanation else 'Report'}..."):
            st.write(a.explanation or "No summary available.")
