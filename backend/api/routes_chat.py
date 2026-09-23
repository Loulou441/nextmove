"""
Route de chat conversationnel avec le coach IA — inspirée de l'expérience
iOS (échange libre, multi-tours) mais ancrée sur les vraies données du match
et le RAG (exercices validés), contrairement au chat iOS qui n'utilise ni
l'un ni l'autre.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user
from backend.db.models import User, Match
from backend.config import PROMPT_PATHS, MODEL_NAME_PADEL, MODEL_NAME_PICKELBALL, MODEL_NAME_TENNIS, GROQ_TEMPERATURE
from backend.agents.agentmanager.agent import Agent
from backend.agents.agentmanager.schemas import ChatReply
from backend.agents.agentmanager.rag import get_knowledge_base
from backend.agents.agentmoderator.agent_moderator import Moderator

router = APIRouter(prefix="/matches", tags=["chat"])

_KNOWLEDGE_FILES = {
    "padel": "knowledge_padel.json",
    "pickleball": "knowledge_pickelball.json",
    "tennis": "knowledge_tennis.json",
}
_CONTEXT_FILES = {
    "padel": "context_padel.txt",
    "pickleball": "context_pickelball.txt",
    "tennis": "context_tennis.txt",
}
_MODEL_NAMES = {
    "padel": MODEL_NAME_PADEL,
    "pickleball": MODEL_NAME_PICKELBALL,
    "tennis": MODEL_NAME_TENNIS,
}


def _extract_persona(context_text: str) -> str:
    """Isole le paragraphe d'identité/personnalité du coach (section 1),
    sans le format de sortie JSON strict qui suit (section 2+), non
    pertinent pour une réponse de chat en texte libre."""
    marker = "2. Cadre d'Analyse"
    idx = context_text.find(marker)
    return context_text[:idx].strip() if idx != -1 else context_text.strip()


class ChatMessage(BaseModel):
    role: str  # "user" ou "coach"
    text: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


@router.post("/{match_id}/chat", response_model=ChatResponse)
def chat_with_coach(
    match_id: str,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Chat libre et multi-tours avec le coach IA, ancré sur les vraies
    métriques du match et sur des exercices réels retrouvés par RAG —
    contrairement au chat iOS, plus simple, qui n'utilise ni l'un ni l'autre.
    """
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")

    sport = match.sport
    if sport not in _CONTEXT_FILES:
        raise HTTPException(status_code=400, detail=f"Sport non supporté : {sport}")

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide.")

    # Modération — même politique de repli que pour le rapport ponctuel :
    # en cas de panne, on bloque par sécurité plutôt que de laisser passer.
    try:
        moderation = Moderator().moderate(message)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le modérateur est momentanément indisponible, réessaie dans un instant.",
        )
    if moderation.is_prompt_injection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce message ressemble à une tentative de manipulation de l'IA et a été bloqué.",
        )

    prompt_dir: Path = PROMPT_PATHS[sport]
    with open(prompt_dir / _CONTEXT_FILES[sport], encoding="utf-8") as f:
        persona = _extract_persona(f.read())

    # Ancrage RAG : cherche des exercices pertinents par rapport au message
    # ET aux difficultés déjà identifiées sur ce match (patterns_summary).
    knowledge_base = get_knowledge_base(sport, prompt_dir / _KNOWLEDGE_FILES[sport])
    pattern_hints = " ".join((match.patterns_summary or {}).get("insights", []))
    query = f"{message} {pattern_hints}".strip()
    drills = knowledge_base.retrieve(query, k=2)
    drills_text = (
        "\n".join(f"- {d['titre']} : {d['description']}" for d in drills)
        if drills else "Aucun exercice spécifique trouvé pour cette question."
    )

    match_summary = (
        f"Sport : {sport}. Note globale : {match.rating}/5. "
        f"Rallies : {match.rallies}, winners : {match.winners}, erreurs : {match.errors}, "
        f"couverture de terrain : {match.coverage}%. "
        f"Tendances observées : {pattern_hints or 'aucune'}."
    )

    system_prompt = (
        f"{persona}\n\n"
        f"Tu es en conversation libre avec le joueur à propos de son match. "
        f"Voici un résumé du match : {match_summary}\n\n"
        f"Exercices de référence potentiellement utiles pour cette question :\n{drills_text}\n\n"
        f"Réponds de façon naturelle et encourageante, en 2 à 4 phrases, en tenant compte "
        f"de l'historique de la conversation. Appuie-toi sur les exercices ci-dessus "
        f"UNIQUEMENT s'ils sont réellement pertinents pour la question posée — sinon, "
        f"réponds normalement sans forcer une référence non pertinente. "
        f"Réponds impérativement au format JSON suivant, sans aucun autre texte autour : "
        f'{{"reply": "ta réponse ici"}}'
    )

    messages = [{"role": "system", "content": system_prompt}]
    for turn in payload.history[-10:]:  # fenêtre glissante, comme le fait iOS
        role = "assistant" if turn.role == "coach" else "user"
        messages.append({"role": role, "content": turn.text})
    messages.append({"role": "user", "content": message})

    agent = Agent()
    try:
        result = agent.call_and_validate(
            messages=messages,
            model=_MODEL_NAMES[sport],
            temperature=GROQ_TEMPERATURE,
            schema=ChatReply,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Le coach IA n'a pas pu répondre : {exc}",
        )

    return ChatResponse(reply=result.reply)