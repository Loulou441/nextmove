"""
Dépendances FastAPI partagées — principalement l'authentification par token.

Réutilise TELLES QUELLES les briques existantes :
  - src.auth.tokens.decode_session_token  (même JWT / même SECRET_KEY que Streamlit)
  - src.db.session.SessionLocal           (même base de données)

Conséquence : un token émis pour l'application iOS et un token émis pour le
web sont interchangeables — c'est le même utilisateur, la même session.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.db.models import User
from src.auth.tokens import decode_session_token

# En-tête "Authorization: Bearer <token>" — standard pour les clients natifs.
bearer_scheme = HTTPBearer(auto_error=True)


def get_db():
    """Fournit une session DB par requête, fermée automatiquement à la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Décode le token Bearer, retrouve l'utilisateur en base et le renvoie.
    Lève 401 si le token est absent, invalide ou expiré.
    """
    token = credentials.credentials
    user_id = decode_session_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
        )
    return user
