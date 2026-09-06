"""
Service métier pour les matchs (Match) — création à l'upload, mise à
jour du statut/métriques après l'étape d'analyse.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Match, MatchEvent
from src.services.cv_pipeline import analyze_video, CVPipelineError

__all__ = ["create_pending_match", "mark_match_ready", "get_user_matches", "CVPipelineError"]


def create_pending_match(
    db: Session,
    user_id: str,
    title: str,
    sport: str,
    video_storage_path: str,
) -> Match:
    """Crée un match en attente d'analyse, juste après l'upload de la vidéo."""
    match = Match(
        user_id=user_id,
        title=title,
        sport=sport,
        match_date=datetime.utcnow(),
        status="pending",
        video_storage_path=video_storage_path,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def mark_match_ready(db: Session, match_id: str) -> Match:
    """
    Lance la vraie analyse vidéo (détection YOLO par sport, cf.
    src/services/cv_pipeline.py) et persiste ses résultats sur le match :
    métriques agrégées (rating, rallies, winners, errors, coverage),
    détail par compétence/highlight/insight, résumé de patterns tactiques,
    et les événements de balle bruts dans match_events.

    Lève CVPipelineError (message adapté à un affichage utilisateur direct)
    si la vidéo est illisible ou si aucune balle n'y est détectée — à
    l'appelant (page Upload) de l'afficher plutôt que de laisser planter
    la page.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise ValueError(f"Match {match_id} introuvable")

    result = analyze_video(match.sport, match.video_storage_path)

    match.status = "ready"
    match.rating = result.rating
    match.rallies = result.rallies
    match.winners = result.winners
    match.errors = result.errors
    match.coverage = result.coverage
    match.skills = result.skills
    match.highlights = result.highlights
    match.insights = result.insights
    match.patterns_summary = result.patterns_summary

    for event in result.events:
        db.add(MatchEvent(
            match_id=match.id,
            event_type=event["event_type"],
            phase=event["phase"],
            minute=event["minute"],
            x=event["x"],
            y=event["y"],
        ))

    db.commit()
    db.refresh(match)
    return match


def get_user_matches(db: Session, user_id: str) -> list[Match]:
    """Retourne tous les matchs d'un utilisateur, les plus récents d'abord."""
    return (
        db.query(Match)
        .filter(Match.user_id == user_id)
        .order_by(Match.created_at.desc())
        .all()
    )
