"""
Routes d'authentification — /auth/register et /auth/login.

Ce ne sont que de fines enveloppes HTTP autour de la logique métier déjà
écrite dans src/auth/service.py. Aucune règle d'authentification n'est
dupliquée ici : on appelle register_user / authenticate_user, puis on émet
le MÊME token JWT que le web (src/auth/tokens.create_session_token).

Le token est renvoyé à la fois dans le corps JSON (pour l'app iOS, qui le
lit et le stocke elle-même) et dans un cookie httpOnly (pour le frontend
web, qui n'a plus besoin de le manipuler manuellement — le navigateur
l'envoie automatiquement à chaque requête).
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user
from api.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse, UpdateUserRequest,
)
from auth.service import (
    register_user, authenticate_user,
    EmailAlreadyExistsError, InvalidCredentialsError,
)
from auth.tokens import create_session_token
from db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 jours, identique à la durée de vie du JWT


def _set_auth_cookie(response: Response, token: str) -> None:
    """
    Pose le cookie httpOnly côté navigateur. En développement local (http),
    `secure=False` est nécessaire — à repasser à True dès qu'un vrai
    déploiement HTTPS est en place.
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,  # TODO: passer à True en production (HTTPS)
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """Crée un compte puis connecte immédiatement l'utilisateur (renvoie un token)."""
    try:
        user = register_user(
            db, payload.email, payload.password, payload.preferred_sport
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    token = create_session_token(user.id)
    _set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Vérifie les identifiants et renvoie un token de session (valable 7 jours)."""
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )

    token = create_session_token(user.id)
    _set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
def logout(response: Response):
    """Efface le cookie de session côté navigateur."""
    response.delete_cookie(COOKIE_NAME)
    return {"status": "ok"}


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