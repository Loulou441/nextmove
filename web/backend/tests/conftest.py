"""
Fixtures partagées pour les tests de routes API.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """
    Client de test FastAPI. dependency_overrides est réinitialisé après
    chaque test pour ne pas faire fuiter les mocks d'un test à l'autre.
    """
    yield TestClient(app)
    app.dependency_overrides.clear()