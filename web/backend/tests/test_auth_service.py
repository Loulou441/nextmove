"""
Tests unitaires pour auth/service.py — la base de données et le hashing de
mot de passe sont simulés (mock), pour tester uniquement la logique métier
(email déjà pris, identifiants invalides) sans dépendre de Supabase.
"""
from unittest.mock import MagicMock, patch

import pytest

from auth.service import (
    register_user, authenticate_user,
    EmailAlreadyExistsError, InvalidCredentialsError,
)


def _mock_db_returning(existing_user):
    """Construit une session DB simulée dont .query().filter().first() renvoie existing_user."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = existing_user
    return db


@patch("auth.service.hash_password", return_value="hashed-password")
def test_register_user_success(mock_hash):
    """Un email inédit doit créer l'utilisateur normalement."""
    db = _mock_db_returning(None)  # aucun utilisateur existant avec cet email

    register_user(db, "nouveau@test.com", "motdepasse123", "padel")

    db.add.assert_called_once()
    db.commit.assert_called_once()
    mock_hash.assert_called_once_with("motdepasse123")


def test_register_user_email_already_exists():
    """Un email déjà présent en base doit lever EmailAlreadyExistsError."""
    fake_existing_user = MagicMock()
    db = _mock_db_returning(fake_existing_user)

    with pytest.raises(EmailAlreadyExistsError):
        register_user(db, "deja-pris@test.com", "motdepasse123")


@patch("auth.service.verify_password", return_value=True)
def test_authenticate_user_success(mock_verify):
    """Bon email + bon mot de passe doit renvoyer l'utilisateur."""
    fake_user = MagicMock(password_hash="hashed-password")
    db = _mock_db_returning(fake_user)

    result = authenticate_user(db, "test@test.com", "bon-mot-de-passe")

    assert result is fake_user
    mock_verify.assert_called_once_with("bon-mot-de-passe", "hashed-password")


def test_authenticate_user_unknown_email():
    """Un email qui n'existe pas en base doit lever InvalidCredentialsError."""
    db = _mock_db_returning(None)

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(db, "inconnu@test.com", "peu-importe")


@patch("auth.service.verify_password", return_value=False)
def test_authenticate_user_wrong_password(mock_verify):
    """Un mauvais mot de passe doit lever InvalidCredentialsError, même avec un email valide."""
    fake_user = MagicMock(password_hash="hashed-password")
    db = _mock_db_returning(fake_user)

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(db, "test@test.com", "mauvais-mot-de-passe")