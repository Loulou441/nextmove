"""
Route de coaching IA — génère un rapport pour un événement réellement détecté
lors de l'analyse vidéo (pas un formulaire de saisie manuelle), avec une
question libre optionnelle filtrée par l'agent modérateur.
"""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user
from db.models import User, Match, MatchEvent
from services.analysis_service import save_analysis
from config import PROMPT_PATHS
from agents.agentmoderator.agent_moderator import Moderator

router = APIRouter(prefix="/matches", tags=["coach"])

_CONTEXT_FILES = {
    "padel": ("context_padel.txt", "user_prompt_padel.txt"),
    "pickleball": ("context_pickelball.txt", "user_prompt_pickelball.txt"),
    "tennis": ("context_tennis.txt", "user_prompt_tennis.txt"),
}

_EVENT_LABELS = {
    "padel": {"WINNER": "Amortie gagnante", "ERROR": "Faute directe au filet", "SHOT": "Échange en jeu"},
    "pickleball": {"WINNER": "Winner Shot", "ERROR": "Rally Error", "SHOT": "Échange en jeu"},
    "tennis": {"WINNER": "Ace", "ERROR": "Double faute", "SHOT": "Échange en jeu"},
}


def _get_coach_class(sport: str):
    if sport == "padel":
        from agents.agentpadel.agent_recommendation_padel import PadelCoachAI
        return PadelCoachAI
    if sport == "pickleball":
        from agents.agentpickelball.agent_recommendation_pickelball import PickelballCoachAI
        return PickelballCoachAI
    if sport == "tennis":
        from agents.agenttennis.agent_recommendation_tennis import TennisCoachAI
        return TennisCoachAI
    raise HTTPException(status_code=400, detail=f"Sport non supporté : {sport}")


class CoachReportRequest(BaseModel):
    event_id: str
    question: str | None = None


@router.post("/{match_id}/coach-report")
def generate_coach_report(
    match_id: str,
    payload: CoachReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")

    event = (
        db.query(MatchEvent)
        .filter(MatchEvent.id == payload.event_id, MatchEvent.match_id == match_id)
        .first()
    )
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Événement introuvable")

    sport = match.sport
    if sport not in _CONTEXT_FILES:
        raise HTTPException(status_code=400, detail=f"Sport non supporté : {sport}")

    question = (payload.question or "").strip()
    if question:
        try:
            moderation = Moderator().moderate(question)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le modérateur est momentanément indisponible, réessaie dans un instant.",
            )
        if moderation.is_prompt_injection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cette question ressemble à une tentative de manipulation de l'IA et a été bloquée. Reformule-la comme une question de coaching normale.",
            )

    prompt_dir: Path = PROMPT_PATHS[sport]
    context_file, prompt_file = _CONTEXT_FILES[sport]

    with open(prompt_dir / "example_entry.json", encoding="utf-8") as f:
        match_data = json.load(f)
    with open(prompt_dir / context_file, encoding="utf-8") as f:
        context = f.read()
    with open(prompt_dir / prompt_file, encoding="utf-8") as f:
        base_prompt = f.read()

    label = _EVENT_LABELS.get(sport, {}).get(event.event_type, event.event_type or "Séquence")
    match_data["donnees_sequences"] = [{
        "id_sequence": f"evt_{event.id}",
        "timestamp": f"{event.minute}:00" if event.minute is not None else "0:00",
        "evenement_cle": label,
        "metriques_video": {
            "position_pieds": {"x": event.x, "y": event.y},
            "phase": event.phase,
        },
        "contexte_tactique": (
            f"Séquence détectée automatiquement par l'analyse vidéo "
            f"(phase de jeu : {event.phase or 'non déterminée'})."
        ),
    }]

    user_prompt = f"{base_prompt}\nVoici les données du match : {match_data}"
    if question:
        user_prompt += f"\n\nQuestion posée par le joueur : {question}"

    CoachClass = _get_coach_class(sport)
    coach = CoachClass(context, user_prompt)

    try:
        recommendations = coach.generate_recommendations(match_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Le coach IA n'a pas pu générer de rapport : {exc}",
        )

    recommendations_dict = recommendations.model_dump()
    save_analysis(db, match_id, recommendations_dict)

    return recommendations_dict