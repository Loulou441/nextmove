"""
Service pour sauvegarder et relire les plans d'entraînement générés,
liés à un utilisateur (pas à un match précis — un plan est une synthèse
globale par sport).
"""

from sqlalchemy.orm import Session

from src.db.models import TrainingPlan


def save_training_plan(db: Session, user_id: str, sport: str, content: dict) -> TrainingPlan:
    """Sauvegarde un plan d'entraînement généré, lié à l'utilisateur et au sport."""
    plan = TrainingPlan(user_id=user_id, sport=sport, content=content)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_user_training_plans(db: Session, user_id: str, sport: str | None = None) -> list[TrainingPlan]:
    """Retourne l'historique des plans d'un utilisateur, les plus récents d'abord.
    Filtre par sport si précisé."""
    query = db.query(TrainingPlan).filter(TrainingPlan.user_id == user_id)
    if sport:
        query = query.filter(TrainingPlan.sport == sport)
    return query.order_by(TrainingPlan.created_at.desc()).all()