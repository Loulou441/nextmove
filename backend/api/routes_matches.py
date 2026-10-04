"""
Routes des matchs — /matches (liste, création + upload, déclenchement de
l'analyse, dashboard détaillé, événements détectés).

Protégé par token : on ne renvoie/modifie que les matchs appartenant à
l'utilisateur déduit du JWT. Réutilise services/match_service.py et
services/video_storage.py.
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.api.deps import get_db, get_current_user
from backend.api.schemas import MatchResponse, MatchDetailResponse, MatchEventResponse, MatchSyncRequest
from backend.db.models import User, Match, MatchEvent
from backend.db.session import SessionLocal
from backend.services.match_service import get_user_matches, create_pending_match, mark_match_ready, CVPipelineError
from backend.services.video_storage import upload_video, VideoTooLargeError, delete_video, get_video_url
from collections import defaultdict

router = APIRouter(prefix="/matches", tags=["matches"])


# Mappe le tag d'un temps fort (highlight) envoyé par l'app mobile vers un
# type d'événement stocké en base. Les temps forts SONT les événements réels
# détectés par l'analyse locale (Core ML). On les persiste comme MatchEvent
# pour que le générateur de programme d'entraînement (qui interroge les
# WINNER/ERROR) ait de quoi travailler après une synchro mobile.
_HIGHLIGHT_TAG_TO_EVENT_TYPE = {
    "winner": "WINNER",
    "error": "ERROR",
    "longrally": "SHOT",
    "long rally": "SHOT",
    "attack": "SHOT",
    "greatdefense": "SHOT",
    "great defense": "SHOT",
}


def _parse_minute(time_str) -> int | None:
    """Convertit un timestamp "m:ss" (ou "mm:ss") en minutes entières."""
    if not isinstance(time_str, str):
        return None
    head = time_str.split(":", 1)[0].strip()
    return int(head) if head.isdigit() else None


def _events_from_highlights(match_id: str, highlights) -> list[MatchEvent]:
    """
    Dérive des MatchEvent à partir des temps forts synchronisés. Sans ça, un
    match synchronisé depuis mobile n'a aucun événement, et la génération de
    programme échoue avec « Aucun événement exploitable ».
    """
    events: list[MatchEvent] = []
    for h in (highlights or []):
        if not isinstance(h, dict):
            continue
        tag = str(h.get("tag", "")).strip().lower()
        event_type = _HIGHLIGHT_TAG_TO_EVENT_TYPE.get(tag, "SHOT")
        events.append(MatchEvent(
            match_id=match_id,
            event_type=event_type,
            phase=h.get("phase"),
            minute=_parse_minute(h.get("time")),
            x=h.get("x"),
            y=h.get("y"),
        ))
    return events


@router.get("", response_model=list[MatchResponse])
def list_my_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les matchs de l'utilisateur connecté (les mêmes que sur le web)."""
    matches = get_user_matches(db, current_user.id)
    return [MatchResponse.model_validate(m) for m in matches]


@router.get("/stats/aggregate")
def get_match_stats(
    sport: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Agrège plusieurs matchs prêts en une seule réponse : évolution note/
    couverture/winners/erreurs dans le temps, compétences moyennes, et
    répartition phase/zone cumulée. Calculé côté serveur pour éviter au
    frontend de faire une requête par match.
    """
    query = db.query(Match).filter(Match.user_id == current_user.id, Match.status == "ready")
    if sport:
        query = query.filter(Match.sport == sport)
    matches = query.order_by(Match.match_date, Match.created_at).all()

    timeline = [
        {
            "match_id": m.id,
            "title": m.title,
            "sport": m.sport,
            "date": (m.match_date or m.created_at).isoformat(),
            "rating": m.rating,
            "coverage": m.coverage,
            "rallies": m.rallies,
            "winners": m.winners,
            "errors": m.errors,
        }
        for m in matches
    ]

    # Moyenne des compétences par libellé, tous matchs confondus (filtrés
    # par sport si demandé) — une compétence absente sur un match n'entre
    # simplement pas dans sa propre moyenne (pas de valeur inventée).
    skill_totals: dict[str, list[float]] = defaultdict(list)
    for m in matches:
        for skill in (m.skills or []):
            label = skill.get("label")
            score = skill.get("score")
            if label and score is not None:
                skill_totals[label].append(score)
    avg_skills = [
        {"label": label, "score": round(sum(scores) / len(scores), 1)}
        for label, scores in skill_totals.items()
    ]

    # Cumul des répartitions phase/zone sur tous les matchs.
    phase_totals: dict[str, int] = defaultdict(int)
    zone_totals: dict[str, int] = defaultdict(int)
    for m in matches:
        patterns = m.patterns_summary or {}
        for phase, count in (patterns.get("phase_distribution") or {}).items():
            phase_totals[phase] += count
        for zone, count in (patterns.get("zone_distribution") or {}).items():
            zone_totals[zone] += count

    ratings = [m.rating for m in matches if m.rating is not None]

    return {
        "timeline": timeline,
        "avg_skills": avg_skills,
        "phase_distribution": dict(phase_totals),
        "zone_distribution": dict(zone_totals),
        "summary": {
            "total_matches": len(matches),
            "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
            "best_match": max(matches, key=lambda m: m.rating or 0).title if matches else None,
        },
    }


@router.post("/sync", response_model=MatchDetailResponse, status_code=status.HTTP_201_CREATED)
def sync_mobile_match(
    payload: MatchSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reçoit le résultat d'une analyse effectuée localement sur l'app mobile
    (Core ML sur l'appareil) et le persiste dans la base partagée.

    Permet à l'utilisateur de retrouver ses analyses mobiles sur le web
    après connexion, sans avoir à uploader la vidéo.
    """
    import uuid
    from datetime import datetime

    match = Match(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=payload.title,
        sport=payload.sport,
        status="ready",
        duration=payload.duration,
        rallies=payload.rallies,
        winners=payload.winners,
        errors=payload.errors,
        coverage=payload.coverage,
        rating=payload.rating,
        skills=payload.skills,
        highlights=payload.highlights,
        insights=payload.insights,
        patterns_summary=payload.patterns_summary,
        match_date=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(match)

    # Persiste les temps forts comme événements pour que la génération de
    # programme d'entraînement dispose de vrais WINNER/ERROR à analyser.
    for event in _events_from_highlights(match.id, payload.highlights):
        db.add(event)

    db.commit()
    db.refresh(match)
    return MatchDetailResponse.model_validate(match)


@router.post("", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    title: str = Form(...),
    sport: str = Form(...),
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Crée un nouveau match : upload la vidéo vers Supabase Storage, puis crée
    l'enregistrement du match en base avec le statut "pending".
    L'analyse (CV) est déclenchée séparément via POST /matches/{id}/analyze.
    """
    file_bytes = await video.read()

    try:
        storage_path = upload_video(current_user.id, video.filename, file_bytes)
    except VideoTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        )

    match = create_pending_match(
        db=db,
        user_id=current_user.id,
        title=title,
        sport=sport,
        video_storage_path=storage_path,
    )
    return MatchResponse.model_validate(match)


def _run_analysis_in_background(match_id: str):
    """
    Exécutée après l'envoi de la réponse HTTP, dans une session DB dédiée
    (la session injectée par requête est fermée avant que cette tâche ne
    s'exécute — on ne peut pas la réutiliser).
    """
    db = SessionLocal()
    try:
        mark_match_ready(db, match_id)
    except CVPipelineError as exc:
        match = db.query(Match).filter(Match.id == match_id).first()
        if match is not None:
            match.status = "failed"
            match.insights = [{"color": "red", "text": str(exc)}]
            db.commit()
    except Exception as exc:
        # Filet de sécurité : toute autre erreur inattendue ne doit pas
        # laisser le match bloqué indéfiniment sur "processing".
        match = db.query(Match).filter(Match.id == match_id).first()
        if match is not None:
            match.status = "failed"
            match.insights = [{"color": "red", "text": f"Erreur inattendue : {exc}"}]
            db.commit()
    finally:
        db.close()


@router.post("/{match_id}/analyze", response_model=MatchResponse, status_code=status.HTTP_202_ACCEPTED)
def analyze_match(
    match_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Déclenche l'analyse CV de la vidéo en tâche de fond et répond
    immédiatement avec le statut "processing". Le frontend doit ensuite
    interroger GET /matches/{id} périodiquement jusqu'à "ready" ou "failed".
    """
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")

    if match.status == "processing":
        return MatchResponse.model_validate(match)  # déjà en cours, on ne relance pas

    match.status = "processing"
    db.commit()
    db.refresh(match)

    background_tasks.add_task(_run_analysis_in_background, match_id)

    return MatchResponse.model_validate(match)


@router.get("/{match_id}", response_model=MatchDetailResponse)
def get_match_detail(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Détail complet d'un match (dashboard) : métriques, skills, highlights,
    insights, patterns. Inclut le message d'erreur si status == 'failed'."""
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")
    return MatchDetailResponse.model_validate(match)

@router.get("/{match_id}/video-url")
def get_match_video_url(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Renvoie une URL signée temporaire pour lire la vidéo du match, sans
    jamais exposer le bucket Storage publiquement. Absente pour les matchs
    synchronisés depuis l'app mobile, qui n'ont pas de vidéo côté serveur.
    """
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")

    if not match.video_storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune vidéo associée à ce match (probablement synchronisé depuis l'app mobile).",
        )

    url = get_video_url(match.video_storage_path)
    return {"video_url": url}

@router.get("/{match_id}/events", response_model=list[MatchEventResponse])
def list_match_events(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Liste les événements détectés automatiquement lors de l'analyse vidéo
    (winners, errors, shots) — sert à peupler le sélecteur du Coach Chat.
    """
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")

    events = (
        db.query(MatchEvent)
        .filter(MatchEvent.match_id == match_id)
        .order_by(MatchEvent.minute)
        .all()
    )
    return [MatchEventResponse.model_validate(e) for e in events]


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Supprime un match, ses données associées, et la vidéo en Storage."""
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")

    storage_path = match.video_storage_path

    db.delete(match)
    db.commit()

    # Nettoyage best-effort : la suppression en base a déjà réussi (ce qui
    # compte le plus pour l'utilisateur) — si le nettoyage Storage échoue
    # (réseau, fichier déjà absent...), on ne fait pas échouer la requête.
    try:
        delete_video(storage_path)
    except Exception as exc:
        logging.getLogger("nextmove.cleanup").warning(
            "Échec de la suppression de la vidéo Storage (%s) pour le match %s : %s",
            storage_path, match_id, exc,
        )