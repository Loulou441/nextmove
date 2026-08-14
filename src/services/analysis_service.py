"""
Service pour sauvegarder et relire les rapports d'analyse IA (table Analysis),
liés à un match précis.
"""

from sqlalchemy.orm import Session

from src.db.models import Analysis, Match


def save_analysis(db: Session, match_id: str, recommendations: dict) -> Analysis:
    """
    Sauvegarde un rapport généré par l'agent IA, lié à un match.
    `recommendations` est stocké tel quel (JSON complet), pour ne rien perdre
    du contenu généré même si sa structure évolue plus tard.
    """
    first_rec = (recommendations.get("recommandations_coach") or [{}])[0]
    contenu = first_rec.get("contenu", {})

    analysis = Analysis(
        match_id=match_id,
        explanation=contenu.get("analyse"),
        recommendations=recommendations,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_match_analyses(db: Session, match_id: str) -> list[Analysis]:
    """Retourne l'historique des rapports générés pour un match, les plus récents d'abord."""
    return (
        db.query(Analysis)
        .filter(Analysis.match_id == match_id)
        .order_by(Analysis.created_at.desc())
        .all()
    )