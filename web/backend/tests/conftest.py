"""
Fixtures partagées pour les tests de routes API.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.deps import get_db, get_current_user


@pytest.fixture
def client():
    """
    Client de test FastAPI. dependency_overrides est réinitialisé après
    chaque test pour ne pas faire fuiter les mocks d'un test à l'autre.
    """
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def fake_user():
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@nextmove.com"
    return user


@pytest.fixture
def authenticated_client(client, fake_user):
    """Client avec get_current_user déjà simulé — pour les routes protégées
    où l'identité de l'utilisateur importe peu, seul l'accès compte."""
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return client


def make_fake_db(query_results: dict):
    """
    Construit une session DB simulée. `query_results` fait correspondre un
    modèle SQLAlchemy (ex. Match) à l'objet que .filter(...).first() doit
    renvoyer pour ce modèle — None pour simuler un "introuvable".
    Clé (Model, "all") pour simuler .filter(...).order_by(...).all().
    """
    db = MagicMock()

    def query_side_effect(model):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = query_results.get(model)
        mock_query.filter.return_value.order_by.return_value.all.return_value = (
            query_results.get((model, "all"), [])
        )
        return mock_query

    db.query.side_effect = query_side_effect
    return db


def override_db(app_, fake_db):
    app_.dependency_overrides[get_db] = lambda: fake_db