"""
Route de génération de plan d'entraînement — synthèse hebdomadaire construite
à partir des vrais événements détectés sur les matchs récents de l'utilisateur
pour un sport donné (pas un exemple générique statique).
"""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user
from backend.db.models import User, Match, MatchEvent
from backend.services.training_plan_service import save_training_plan, get_user_training_plans
from backend.config import PROMPT_PATHS

router = APIRouter(prefix="/training-plan", tags=["training-plan"])

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

MAX_EVENTS_FOR_PLAN = 6  # on ne surcharge pas le prompt avec tous les événements bruts


def _get_coach_class(sport: str):
    if sport == "padel":
        from backend.agents.agentpadel.agent_recommendation_padel import PadelCoachAI
        return PadelCoachAI
    if sport == "pickleball":
        from backend.agents.agentpickelball.agent_recommendation_pickelball import PickelballCoachAI
        return PickelballCoachAI
    if sport == "tennis":
        from backend.agents.agenttennis.agent_recommendation_tennis import TennisCoachAI
        return TennisCoachAI
    raise HTTPException(status_code=400, detail=f"Sport non supporté : {sport}")


class TrainingPlanRequest(BaseModel):
    sport: str


class TrainingPlanResponse(BaseModel):
    id: str
    sport: str
    content: dict

    class Config:
        from_attributes = True


@router.post("", response_model=TrainingPlanResponse, status_code=status.HTTP_201_CREATED)
def generate_training_plan(
    payload: TrainingPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Génère un programme d'entraînement hebdomadaire à partir des événements
    (winners/errors) réellement détectés sur les matchs "ready" les plus
    récents de l'utilisateur pour ce sport.
    """
    sport = payload.sport
    if sport not in _CONTEXT_FILES:
        raise HTTPException(status_code=400, detail=f"Sport non supporté : {sport}")

    recent_matches = (
        db.query(Match)
        .filter(Match.user_id == current_user.id, Match.sport == sport, Match.status == "ready")
        .order_by(Match.match_date.desc())
        .limit(5)
        .all()
    )
    if not recent_matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun match analysé pour le sport '{sport}' — analyse au moins un match avant de générer un programme.",
        )

    match_ids = [m.id for m in recent_matches]
    events = (
        db.query(MatchEvent)
        .filter(MatchEvent.match_id.in_(match_ids), MatchEvent.event_type.in_(["WINNER", "ERROR"]))
        .order_by(MatchEvent.minute.desc())
        .limit(MAX_EVENTS_FOR_PLAN)
        .all()
    )
    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun événement exploitable trouvé sur les matchs récents pour ce sport.",
        )

    prompt_dir: Path = PROMPT_PATHS[sport]
    context_file, prompt_file = _CONTEXT_FILES[sport]

    with open(prompt_dir / "example_entry.json", encoding="utf-8") as f:
        match_data = json.load(f)
    with open(prompt_dir / context_file, encoding="utf-8") as f:
        context = f.read()
    with open(prompt_dir / prompt_file, encoding="utf-8") as f:
        base_prompt = f.read()

    labels = _EVENT_LABELS.get(sport, {})
    match_data["donnees_sequences"] = [
        {
            "id_sequence": f"evt_{e.id}",
            "timestamp": f"{e.minute}:00" if e.minute is not None else "0:00",
            "evenement_cle": labels.get(e.event_type, e.event_type or "Séquence"),
            "metriques_video": {
                "position_pieds": {"x": e.x, "y": e.y},
                "phase": e.phase,
            },
            "contexte_tactique": (
                f"Séquence détectée automatiquement sur un match récent "
                f"(phase de jeu : {e.phase or 'non déterminée'})."
            ),
        }
        for e in events
    ]

    user_prompt = f"{base_prompt}\nVoici l'intégralité des données du match : {match_data}"

    CoachClass = _get_coach_class(sport)
    coach = CoachClass(context, user_prompt)

    try:
        recommendations = coach.generate_recommendations(match_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Le coach IA n'a pas pu générer de programme : {exc}",
        )

    recommendations_dict = recommendations.model_dump()
    plan = save_training_plan(db, current_user.id, sport, recommendations_dict)

    return TrainingPlanResponse(id=plan.id, sport=plan.sport, content=plan.content)


@router.get("", response_model=list[TrainingPlanResponse])
def list_training_plans(
    sport: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Historique des programmes générés pour l'utilisateur (filtrable par sport)."""
    plans = get_user_training_plans(db, current_user.id, sport=sport)
    return [TrainingPlanResponse(id=p.id, sport=p.sport, content=p.content) for p in plans]