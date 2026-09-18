"""
Service métier des matchs Streamlit.

Le comportement est aligné autant que possible sur les états utilisés par
RecordingCard.swift : pending -> processing -> ready, avec failed en cas
d'erreur. Aucun changement n'est requis côté Swift ni dans le schéma SQL.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Match, MatchEvent
from src.services.cv_pipeline import analyze_video, CVPipelineError

__all__ = [
    "create_pending_match",
    "mark_match_ready",
    "get_user_matches",
    "delete_match",
    "CVPipelineError",
]


def create_pending_match(
    db: Session,
    user_id: str,
    title: str,
    sport: str,
    video_storage_path: str,
) -> Match:
    """Crée un enregistrement en attente, comme un GameRecording pending."""
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
    """Analyse un match en exposant les mêmes états visuels que l'app Swift."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise ValueError(f"Match {match_id} introuvable")

    match.status = "processing"
    db.commit()

    try:
        # Swift réutilise le détecteur Tennis pour Badminton.
        # On reproduit uniquement cette compatibilité côté Streamlit sans
        # toucher au projet iOS ni aux poids existants.
        analysis_sport = "tennis" if match.sport == "badminton" else match.sport
        result = analyze_video(analysis_sport, match.video_storage_path)

        # Nettoie d'éventuels événements issus d'une tentative précédente.
        db.query(MatchEvent).filter(MatchEvent.match_id == match.id).delete()

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
            db.add(
                MatchEvent(
                    match_id=match.id,
                    event_type=event["event_type"],
                    phase=event["phase"],
                    minute=event["minute"],
                    x=event["x"],
                    y=event["y"],
                )
            )

        db.commit()
        db.refresh(match)
        return match
    except Exception:
        db.rollback()
        match = db.query(Match).filter(Match.id == match_id).first()
        if match is not None:
            match.status = "failed"
            db.commit()
        raise


def get_user_matches(db: Session, user_id: str) -> list[Match]:
    """Retourne les matchs d'un utilisateur, du plus récent au plus ancien."""
    return (
        db.query(Match)
        .filter(Match.user_id == user_id)
        .order_by(Match.created_at.desc())
        .all()
    )


def delete_match(db: Session, match_id: str, user_id: str) -> bool:
    """Supprime un match appartenant à l'utilisateur courant."""
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == user_id)
        .first()
    )
    if match is None:
        return False
    db.delete(match)
    db.commit()
    return True
