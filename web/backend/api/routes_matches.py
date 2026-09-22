"""
Routes des matchs — /matches (liste, création + upload, déclenchement de
l'analyse, dashboard détaillé, événements détectés).

Protégé par token : on ne renvoie/modifie que les matchs appartenant à
l'utilisateur déduit du JWT. Réutilise services/match_service.py et
services/video_storage.py.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user
from api.schemas import MatchResponse, MatchDetailResponse, MatchEventResponse
from db.models import User, Match, MatchEvent
from db.session import SessionLocal
from services.match_service import get_user_matches, create_pending_match, mark_match_ready, CVPipelineError
from services.video_storage import upload_video, VideoTooLargeError

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchResponse])
def list_my_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les matchs de l'utilisateur connecté (les mêmes que sur le web)."""
    matches = get_user_matches(db, current_user.id)
    return [MatchResponse.model_validate(m) for m in matches]


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
    """Supprime un match et ses données associées (événements, analyses)."""
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")

    db.delete(match)
    db.commit()