"""
Routes des matchs — /matches (liste des matchs de l'utilisateur connecté).

Protégé par token : on ne renvoie que les matchs appartenant à l'utilisateur
déduit du JWT. Réutilise src.services.match_service.get_user_matches.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_user
from src.api.schemas import MatchResponse
from src.db.models import User
from src.services.match_service import get_user_matches

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchResponse])
def list_my_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les matchs de l'utilisateur connecté (les mêmes que sur le web)."""
    matches = get_user_matches(db, current_user.id)
    return [MatchResponse.model_validate(m) for m in matches]
