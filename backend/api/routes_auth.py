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

Vérification d'email et mot de passe oublié : un code à 6 chiffres est
envoyé par email (services/email_service.py) et stocké dans la table
verification_codes, avec une expiration courte et un usage unique.
"""
import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user
from backend.api.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse, UpdateUserRequest,
)
from backend.auth.service import (
    register_user, authenticate_user,
    EmailAlreadyExistsError, InvalidCredentialsError,
)
from backend.auth.tokens import create_session_token, SESSION_DURATION_DAYS
from backend.auth.security import hash_password
from backend.config import AUTH_COOKIE_NAME, AUTH_COOKIE_SECURE, AUTH_COOKIE_SAMESITE
from backend.db.models import User, VerificationCode
from backend.services.email_service import send_verification_code, send_password_reset_code, EmailSendError
router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = AUTH_COOKIE_NAME
COOKIE_MAX_AGE = 60 * 60 * 24 * SESSION_DURATION_DAYS  # 7 jours, identique à la durée de vie du JWT

CODE_VALIDITY_MINUTES = 15


def _set_auth_cookie(response: Response, token: str) -> None:
    """Pose le cookie selon la configuration locale ou HTTPS du déploiement."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite=AUTH_COOKIE_SAMESITE,
        secure=AUTH_COOKIE_SECURE,
    )


def _generate_code() -> str:
    """Code à 6 chiffres, par ex. '042817'."""
    return "".join(random.choices(string.digits, k=6))


def _create_and_send_code(db: Session, user: User, purpose: str) -> None:
    """
    Crée un nouveau code en base et l'envoie par email. Les anciens codes
    non utilisés du même type ne sont pas supprimés (ils expireront
    naturellement), mais seul le plus récent pourra être validé.
    """
    code = _generate_code()
    verification = VerificationCode(
        user_id=user.id,
        code=code,
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=CODE_VALIDITY_MINUTES),
    )
    db.add(verification)
    db.commit()

    try:
        if purpose == "email_verification":
            send_verification_code(user.email, code)
        else:
            send_password_reset_code(user.email, code)
    except EmailSendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Impossible d'envoyer l'email : {exc}",
        )


def _consume_code(db: Session, user: User, purpose: str, code: str) -> None:
    """
    Vérifie un code (le plus récent non utilisé, non expiré, pour ce purpose)
    et le marque comme utilisé. Lève 400 si invalide/expiré/déjà utilisé.
    """
    verification = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.user_id == user.id,
            VerificationCode.purpose == purpose,
            VerificationCode.used_at.is_(None),
        )
        .order_by(VerificationCode.created_at.desc())
        .first()
    )
    if verification is None or verification.code != code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code invalide.")
    if verification.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce code a expiré.")

    verification.used_at = datetime.utcnow()
    db.commit()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """
    Crée un compte (non vérifié) puis connecte immédiatement l'utilisateur,
    et envoie un code de confirmation par email. Le compte reste utilisable
    tel quel (pas de blocage strict) ; `email_verified` sert d'indicateur
    côté frontend pour inviter à confirmer.
    """
    try:
        user = register_user(
            db, payload.email, payload.password, payload.preferred_sport
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    _create_and_send_code(db, user, purpose="email_verification")

    token = create_session_token(user.id)
    _set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


class VerifyEmailRequest(BaseModel):
    code: str


@router.post("/verify-email")
def verify_email(
    payload: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirme l'email du compte connecté à partir du code reçu."""
    _consume_code(db, current_user, purpose="email_verification", code=payload.code)
    current_user.email_verified = True
    db.commit()
    return {"status": "ok"}


@router.post("/resend-verification")
def resend_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Renvoie un nouveau code de confirmation (si pas déjà vérifié)."""
    if current_user.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà confirmé.")
    _create_and_send_code(db, current_user, purpose="email_verification")
    return {"status": "ok"}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Envoie un code de réinitialisation si l'email existe. Répond toujours
    de la même façon, qu'un compte existe ou non avec cet email, pour ne
    pas révéler quelles adresses sont enregistrées.
    """
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if user is not None:
        _create_and_send_code(db, user, purpose="password_reset")
    return {"status": "ok"}


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Vérifie le code reçu par email et définit un nouveau mot de passe."""
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code invalide.")

    _consume_code(db, user, purpose="password_reset", code=payload.code)

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"status": "ok"}


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
    response.delete_cookie(COOKIE_NAME, httponly=True,
                           secure=AUTH_COOKIE_SECURE, samesite=AUTH_COOKIE_SAMESITE)
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
