"""
Service d'authentification — logique métier d'inscription et de connexion.

Fait le lien entre la BDD (modèle User) et le hashing des mots de passe.
Ne gère PAS les cookies/sessions Streamlit — ça, c'est le rôle de
session_manager.py.
"""

from sqlalchemy.orm import Session

from src.db.models import User
from src.auth.security import hash_password, verify_password


class EmailAlreadyExistsError(Exception):
    """Levée quand on tente de créer un compte avec un email déjà utilisé."""
    pass


class InvalidCredentialsError(Exception):
    """Levée quand l'email n'existe pas ou le mot de passe est incorrect."""
    pass


def register_user(db: Session, email: str, password: str, preferred_sport: str = "pickleball") -> User:
    """
    Crée un nouvel utilisateur.
    Lève EmailAlreadyExistsError si l'email est déjà pris.
    """
    email_normalized = email.strip().lower()

    existing = db.query(User).filter(User.email == email_normalized).first()
    if existing is not None:
        raise EmailAlreadyExistsError(f"Un compte existe déjà avec l'email {email_normalized}")

    user = User(
        email=email_normalized,
        password_hash=hash_password(password),
        preferred_sport=preferred_sport,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Vérifie les identifiants et retourne l'utilisateur si valides.
    Lève InvalidCredentialsError sinon (email inconnu OU mauvais mot de passe —
    volontairement le même message dans les deux cas, pour ne pas révéler
    quels emails existent en base).
    """
    email_normalized = email.strip().lower()
    user = db.query(User).filter(User.email == email_normalized).first()

    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Email ou mot de passe incorrect")

    return user