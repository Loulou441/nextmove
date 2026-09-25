"""
Tests unitaires pour les schémas Pydantic (api/schemas.py) — validation pure,
aucune dépendance à la base de données ou au réseau.
"""
import pytest
from pydantic import ValidationError

from api.schemas import RegisterRequest, LoginRequest, UpdateUserRequest, UserResponse


def test_register_request_accepts_valid_data():
    """Un email et un mot de passe valides doivent être acceptés tels quels."""
    req = RegisterRequest(email="test@nextmove.com", password="motdepasse123")

    assert req.email == "test@nextmove.com"
    assert req.preferred_sport == "pickleball"  # valeur par défaut


def test_register_request_rejects_invalid_email():
    """Une adresse email mal formée doit être rejetée avant d'atteindre la route."""
    with pytest.raises(ValidationError):
        RegisterRequest(email="pas-un-email", password="motdepasse123")


def test_register_request_rejects_short_password():
    """Un mot de passe de moins de 6 caractères doit être rejeté."""
    with pytest.raises(ValidationError):
        RegisterRequest(email="test@nextmove.com", password="123")


def test_register_request_accepts_custom_sport():
    """Le sport préféré doit pouvoir être explicitement fourni."""
    req = RegisterRequest(email="test@nextmove.com", password="motdepasse123", preferred_sport="padel")

    assert req.preferred_sport == "padel"


def test_login_request_requires_email_and_password():
    """email et password sont obligatoires — les omettre doit lever une erreur."""
    with pytest.raises(ValidationError):
        LoginRequest(email="test@nextmove.com")  # password manquant


def test_update_user_request_accepts_any_sport_string():
    """
    Le schéma ne valide pas la liste des sports autorisés (padel/pickleball/
    tennis) — cette règle vit côté route/logique métier, pas dans le schéma.
    Ce test documente ce choix : un sport arbitraire n'est PAS rejeté ici.
    """
    req = UpdateUserRequest(preferred_sport="sport-quelconque")

    assert req.preferred_sport == "sport-quelconque"


def test_user_response_can_be_built_from_orm_like_object():
    """
    UserResponse doit pouvoir être construit depuis un objet type SQLAlchemy
    (via from_attributes), pas seulement depuis un dict — c'est exactement
    comment les routes l'utilisent (UserResponse.model_validate(user)).
    """
    class FakeOrmUser:
        id = "user-123"
        email = "test@nextmove.com"
        preferred_sport = "padel"
        created_at = "2026-01-01T00:00:00"

    result = UserResponse.model_validate(FakeOrmUser())

    assert result.id == "user-123"
    assert result.preferred_sport == "padel"