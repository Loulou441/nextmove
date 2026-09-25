"""
Dépendances FastAPI partagées — principalement l'authentification par token.

Réutilise TELLES QUELLES les briques existantes :
  - src.auth.tokens.decode_session_token  (même JWT / même SECRET_KEY que Streamlit)
  - src.db.session.SessionLocal           (même base de données)

Conséquence : un token émis pour l'application iOS et un token émis pour le
web sont interchangeables — c'est le même utilisateur, la même session.

Deux façons de transmettre le token sont acceptées :
  - En-tête "Authorization: Bearer <token>" — utilisé par l'app iOS (client natif).
  - Cookie httpOnly "access_token" — utilisé par le frontend web (posé par
    /auth/login et /auth/register), plus sûr contre le vol via XSS qu'un
    stockage manuel côté JavaScript.
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import User
from auth.tokens import decode_session_token

# auto_error=False : ne lève pas d'erreur si l'en-tête est absent, pour
# laisser une chance au cookie de fournir le token à la place.
bearer_scheme = HTTPBearer(auto_error=False)

COOKIE_NAME = "access_token"


def get_db():
    """Fournit une session DB par requête, fermée automatiquement à la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Décode le token (en-tête Bearer ou cookie httpOnly), retrouve
    l'utilisateur en base et le renvoie. Lève 401 si le token est absent,
    invalide ou expiré.
    """
    token = credentials.credentials if credentials else request.cookies.get(COOKIE_NAME)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )

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