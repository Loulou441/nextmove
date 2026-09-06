"""
Tokens de session (JWT) — pour garder un utilisateur connecté entre les
rechargements de page via un cookie, sans avoir à retaper son mot de passe.

Le token contient l'id utilisateur + une date d'expiration, signé avec
SECRET_KEY pour empêcher qu'il soit falsifié côté client.
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY manquante dans .env — nécessaire pour signer les sessions. "
        "Génère-en une avec : python -c \"import secrets; print(secrets.token_hex(32))\""
    )

ALGORITHM = "HS256"
SESSION_DURATION_DAYS = 7


def create_session_token(user_id: str) -> str:
    """Génère un token de session signé, valable SESSION_DURATION_DAYS jours."""
    expire = datetime.now(timezone.utc) + timedelta(days=SESSION_DURATION_DAYS)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_session_token(token: str) -> str | None:
    """
    Vérifie et décode un token de session.
    Retourne l'user_id si le token est valide, None s'il est invalide/expiré.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None