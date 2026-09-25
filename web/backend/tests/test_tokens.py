"""
Tests unitaires pour auth/tokens.py — aucune base de données, aucun réseau.
"""
import jwt
import pytest
from datetime import datetime, timedelta, timezone

from auth.tokens import create_session_token, decode_session_token, SECRET_KEY, ALGORITHM


def test_create_and_decode_roundtrip():
    """Un token créé pour un utilisateur doit se décoder vers ce même utilisateur."""
    token = create_session_token("user-123")
    assert decode_session_token(token) == "user-123"


def test_decode_invalid_token_returns_none():
    """Un token mal formé ou signé avec une mauvaise clé ne doit jamais planter."""
    assert decode_session_token("ceci-nest-pas-un-jwt") is None


def test_decode_expired_token_returns_none():
    """Un token dont la date d'expiration est dépassée doit être rejeté."""
    expired_payload = {
        "user_id": "user-123",
        "exp": datetime.now(timezone.utc) - timedelta(days=1),
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    assert decode_session_token(expired_token) is None


def test_decode_token_signed_with_wrong_key_returns_none():
    """Un token falsifié avec une autre clé secrète doit être rejeté."""
    forged_payload = {
        "user_id": "attacker",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    forged_token = jwt.encode(forged_payload, "mauvaise-cle-secrete", algorithm=ALGORITHM)
    assert decode_session_token(forged_token) is None