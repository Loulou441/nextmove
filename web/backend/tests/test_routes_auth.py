"""
Tests d'intégration des routes /auth/* via TestClient — la base de données
et la logique métier (register_user/authenticate_user) sont mockées : aucun
de ces tests ne touche au vrai Supabase.
"""
from unittest.mock import MagicMock, patch

from auth.service import EmailAlreadyExistsError, InvalidCredentialsError


def _fake_user():
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@nextmove.com"
    user.preferred_sport = "padel"
    user.created_at = "2026-01-01T00:00:00"
    return user


@patch("api.routes_auth.create_session_token", return_value="fake-jwt-token")
@patch("api.routes_auth.register_user")
def test_register_success_sets_cookie_and_returns_token(mock_register, mock_token, client):
    """Une inscription réussie doit renvoyer le token en JSON ET poser le cookie httpOnly."""
    mock_register.return_value = _fake_user()

    response = client.post(
        "/auth/register",
        json={"email": "test@nextmove.com", "password": "motdepasse123", "preferred_sport": "padel"},
    )

    assert response.status_code == 201
    assert response.json()["access_token"] == "fake-jwt-token"
    assert "access_token" in response.cookies


@patch("api.routes_auth.register_user")
def test_register_existing_email_returns_409(mock_register, client):
    """Un email déjà pris doit renvoyer 409, pas planter en 500."""
    mock_register.side_effect = EmailAlreadyExistsError("Un compte existe déjà")

    response = client.post(
        "/auth/register",
        json={"email": "deja-pris@test.com", "password": "motdepasse123"},
    )

    assert response.status_code == 409


def test_register_invalid_email_returns_422():
    """Un email mal formé doit être rejeté par la validation Pydantic (422),
    avant même d'atteindre la logique métier."""
    from tests.conftest import app  # évite un import circulaire en tête de fichier
    from fastapi.testclient import TestClient

    response = TestClient(app).post(
        "/auth/register",
        json={"email": "pas-un-email", "password": "motdepasse123"},
    )

    assert response.status_code == 422


@patch("api.routes_auth.create_session_token", return_value="fake-jwt-token")
@patch("api.routes_auth.authenticate_user")
def test_login_success(mock_auth, mock_token, client):
    """Des identifiants valides doivent renvoyer un token et poser le cookie."""
    mock_auth.return_value = _fake_user()

    response = client.post(
        "/auth/login",
        json={"email": "test@nextmove.com", "password": "bon-mot-de-passe"},
    )

    assert response.status_code == 200
    assert "access_token" in response.cookies


@patch("api.routes_auth.authenticate_user")
def test_login_invalid_credentials_returns_401(mock_auth, client):
    """De mauvais identifiants doivent renvoyer 401, sans révéler s'il s'agit
    d'un email inconnu ou d'un mauvais mot de passe."""
    mock_auth.side_effect = InvalidCredentialsError("Email ou mot de passe incorrect")

    response = client.post(
        "/auth/login",
        json={"email": "test@nextmove.com", "password": "mauvais-mot-de-passe"},
    )

    assert response.status_code == 401


def test_me_without_token_returns_401(client):
    """
    Appeler /auth/me sans cookie ni en-tête Authorization doit renvoyer 401
    immédiatement — le code rejette avant même d'interroger la base, donc
    ce test n'a pas besoin de mocker get_db.
    """
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_logout_clears_cookie(client):
    """La déconnexion doit renvoyer 200 et effacer le cookie de session."""
    response = client.post("/auth/logout")

    assert response.status_code == 200
    # Un cookie "effacé" a une date d'expiration passée dans l'en-tête Set-Cookie.
    assert "access_token" in response.headers.get("set-cookie", "")