import streamlit as st

from src.design import SPORTS, page_header, set_ios_design, skill_bar
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.match_service import get_user_matches

set_ios_design()
current_user = get_current_user()
if current_user is None:
    st.stop()

with get_db_session() as db:
    matches = get_user_matches(db, current_user.id)
    for item in matches:
        db.expunge(item)

match_id = st.session_state.get("current_game_id")
match = next((m for m in matches if m.id == match_id and m.status == "ready"), None)

if match is None:
    if st.button("‹ Library", key="coach_missing_back"):
        st.session_state["route"] = "main"
        st.session_state["nav_radio"] = "📚 Library"
        st.rerun()
    page_header("AI Coach")
    st.info("Open an analyzed game from the Library first.")
    st.stop()

sport_info = SPORTS.get(match.sport, SPORTS["pickleball"])
skills = match.skills or []
chat_key = f"coach_messages_{match.id}"

top_left, top_title = st.columns([0.7, 5])
with top_left:
    if st.button("‹ Analysis", key="coach_back"):
        st.session_state["route"] = "analysis"
        st.rerun()
with top_title:
    page_header("AI Coach", f"{match.title} · {sport_info['icon']} {sport_info['label']}")

if chat_key not in st.session_state:
    greeting = (
        f"Hey! I'm your {sport_info['label']} coach. I reviewed your game — "
        f"you're sitting at {float(match.rating or 0):.1f}/5.0 overall. "
        "Ask me anything: what to work on, drills for a weak shot, or how to win more points. "
        "What's on your mind?"
    )
    st.session_state[chat_key] = [{"role": "assistant", "text": greeting}]


def _skill_advice(label: str) -> str:
    name = (label or "skill").lower()
    if "serve" in name:
        return "Focus on depth and consistency before power — a deep serve pushes opponents back."
    if "return" in name:
        return "Return deep and recover quickly so you can take a stronger court position."
    if "third" in name:
        return "Practice a soft third-shot drop so you can move forward safely instead of forcing the attack."
    if "dink" in name:
        return "Soften your grip and keep the ball low; controlled dinks create the attackable ball later."
    if "volley" in name:
        return "Use a short backswing, keep the racket in front, and prioritize clean contact over power."
    if "movement" in name or "position" in name:
        return "Split-step as your opponent hits and recover toward your neutral position after every shot."
    if "forehand" in name or "backhand" in name:
        return "Build consistency with larger targets first, then add pace once your contact point is repeatable."
    if "lob" in name:
        return "Give yourself margin over the opponents and aim deep so the lob buys time to recover position."
    if "smash" in name or "bandeja" in name:
        return "Prioritize balance and placement before maximum power; recover immediately after contact."
    return "Work on repeatable contact, good court position and higher-percentage targets before adding more pace."


def _weakest_skill():
    if not skills:
        return None
    return min(skills, key=lambda item: float(item.get("score", 0)))


def _strongest_skill():
    if not skills:
        return None
    return max(skills, key=lambda item: float(item.get("score", 0)))


def _reply(user_text: str) -> str:
    text = user_text.lower()
    weakest = _weakest_skill()
    strongest = _strongest_skill()

    if any(word in text for word in ["work on", "weak", "improve", "focus"]):
        if weakest:
            label = weakest.get("label", "skill")
            score = float(weakest.get("score", 0))
            return f"Your {label.lower()} is your biggest opportunity right now ({score:.1f}/5.0). {_skill_advice(label)}"
        return f"Your overall rating is {float(match.rating or 0):.1f}/5.0. Focus first on consistency and court position."

    if any(word in text for word in ["drill", "practice", "train"]):
        if weakest:
            label = weakest.get("label", "weakest skill")
            return f"Try a 10-minute {label.lower()} block: repeat the same pattern at controlled pace, aiming for 8 clean repetitions out of 10 before increasing speed. {_skill_advice(label)}"
        return "Try a consistency drill: 3 sets of 10 controlled repetitions, increasing speed only after you hit 8 clean reps in a set."

    if any(word in text for word in ["good", "strength", "best"]):
        if strongest:
            label = strongest.get("label", "skill")
            score = float(strongest.get("score", 0))
            return f"Your {label.lower()} is a real strength ({score:.1f}/5.0). Build your game plan around it and use it to create pressure before you take more risk."
        return "Your overall game is developing well. Use your most reliable pattern to start points and protect it under pressure."

    if any(word in text for word in ["win", "strategy", "point", "beat"]):
        winners = int(match.winners or 0)
        errors = int(match.errors or 0)
        if errors > winners:
            return f"You had {errors} unforced errors vs {winners} winners. To win more points, cut the errors first: use bigger targets and attack only when the ball is genuinely favorable."
        return f"You're generating winners ({winners} vs {errors} errors). Keep using your stronger patterns to create pressure, then finish when you get the right ball."

    if any(word in text for word in ["error", "mistake", "miss"]):
        errors = int(match.errors or 0)
        return f"You made {errors} unforced errors in this game. Reduce them by choosing higher-percentage targets and resetting the rally when you're off balance instead of forcing the next shot."

    if any(word in text for word in ["how did", "overall", "rating", "summary"]):
        return (
            f"Overall you're at {float(match.rating or 0):.1f}/5.0. You played {int(match.rallies or 0)} rallies "
            f"with {int(match.winners or 0)} winners and {int(match.errors or 0)} errors, covering {int(match.coverage or 0)}% of the court. "
            "Ask me what to work on and I'll get specific."
        )

    if weakest:
        label = weakest.get("label", "skill")
        score = float(weakest.get("score", 0))
        return f"The clearest next step from this game is your {label.lower()} ({score:.1f}/5.0). {_skill_advice(label)}"
    return "Ask me about what to work on, a drill, your strengths, or how to win more points and I'll use this game's analysis."


summary_col, chat_col = st.columns([0.8, 1.7], gap="large")

with summary_col:
    st.markdown(
        f"""
        <div class="nm-card coach-summary">
          <div style="font-size:11px;color:#8E8E93;text-transform:uppercase;letter-spacing:.06em;font-weight:650;">Game context</div>
          <div style="font-size:17px;font-weight:700;margin-top:7px;">{match.title}</div>
          <div style="font-size:12px;color:#8E8E93;margin-top:3px;">{sport_info['icon']} {sport_info['label']}</div>
          <div style="display:flex;gap:18px;margin-top:16px;">
            <div><div style="font-size:20px;font-weight:750;">{float(match.rating or 0):.1f}</div><div style="font-size:10px;color:#8E8E93;">Rating</div></div>
            <div><div style="font-size:20px;font-weight:750;">{int(match.rallies or 0)}</div><div style="font-size:10px;color:#8E8E93;">Rallies</div></div>
            <div><div style="font-size:20px;font-weight:750;">{int(match.winners or 0)}</div><div style="font-size:10px;color:#8E8E93;">Winners</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if skills:
        st.markdown('<div class="nm-card" style="margin-top:10px;"><div style="font-size:12px;font-weight:650;margin-bottom:12px;">Skills</div>', unsafe_allow_html=True)
        for skill in skills[:6]:
            skill_bar(
                skill.get("label", "Skill"),
                skill.get("icon", "•"),
                skill.get("score", 0),
                5.0,
                skill.get("color", "green"),
            )
        st.markdown("</div>", unsafe_allow_html=True)

with chat_col:
    st.markdown(
        '<div style="font-size:15px;font-weight:650;margin-bottom:10px;">Conversation</div>',
        unsafe_allow_html=True,
    )

    for message in st.session_state[chat_key]:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            if role == "assistant":
                st.caption(f"Coach · {sport_info['icon']} {sport_info['label']}")
            st.write(message["text"])

    suggested_prompts = [
        "What should I work on?",
        "Give me a drill",
        "How do I win more points?",
        "What am I good at?",
    ]

    cols = st.columns(4)
    for idx, suggested in enumerate(suggested_prompts):
        with cols[idx]:
            if st.button(suggested, key=f"coach_prompt_{idx}", use_container_width=True):
                st.session_state[chat_key].append({"role": "user", "text": suggested})
                st.session_state[chat_key].append({"role": "assistant", "text": _reply(suggested)})
                st.rerun()

    prompt = st.chat_input("Ask your coach...")
    if prompt:
        st.session_state[chat_key].append({"role": "user", "text": prompt})
        st.session_state[chat_key].append({"role": "assistant", "text": _reply(prompt)})
        st.rerun()
