"""
Routes d'authentification — /auth/register et /auth/login.

Ce ne sont que de fines enveloppes HTTP autour de la logique métier déjà
écrite dans src/auth/service.py. Aucune règle d'authentification n'est
dupliquée ici : on appelle register_user / authenticate_user, puis on émet
le MÊME token JWT que le web (src/auth/tokens.create_session_token).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user
from backend.api.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse, UpdateUserRequest,
)
from backend.auth.service import (
    register_user, authenticate_user,
    EmailAlreadyExistsError, InvalidCredentialsError,
)
from backend.auth.tokens import create_session_token
from backend.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Crée un compte puis connecte immédiatement l'utilisateur (renvoie un token)."""
    try:
        user = register_user(
            db, payload.email, payload.password, payload.preferred_sport
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    token = create_session_token(user.id)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Vérifie les identifiants et renvoie un token de session (valable 7 jours)."""
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )

    token = create_session_token(user.id)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Renvoie l'utilisateur associé au token — sert à valider une session iOS."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Met à jour les préférences du profil (pour l'instant : le sport principal)."""
    current_user.preferred_sport = payload.preferred_sport
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)