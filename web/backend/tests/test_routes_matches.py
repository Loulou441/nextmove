"""
Tests d'intégration des routes /matches/* — la base de données et les
services externes (Storage, pipeline CV) sont mockés.
"""
from unittest.mock import MagicMock, patch

from db.models import Match
from tests.conftest import make_fake_db, override_db


@patch("api.routes_matches.get_user_matches", return_value=[])
def test_list_matches_calls_service_with_current_user(mock_service, authenticated_client, fake_user):
    """La liste des matchs doit être demandée pour l'utilisateur courant, pas un autre."""
    response = authenticated_client.get("/matches")

    assert response.status_code == 200
    mock_service.assert_called_once()
    assert mock_service.call_args[0][1] == fake_user.id


def test_get_match_not_found_returns_404(client, fake_user):
    """Un match inexistant (ou appartenant à un autre utilisateur) doit renvoyer 404."""
    from api.main import app
    from api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: fake_user
    override_db(app, make_fake_db({Match: None}))

    response = client.get("/matches/match-inexistant")

    assert response.status_code == 404


def test_delete_match_not_found_returns_404(client, fake_user):
    """Supprimer un match introuvable doit renvoyer 404, pas planter en 500."""
    from api.main import app
    from api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: fake_user
    override_db(app, make_fake_db({Match: None}))

    response = client.delete("/matches/match-inexistant")

    assert response.status_code == 404


@patch("api.routes_matches.delete_video")
def test_delete_match_success_also_cleans_up_video(mock_delete_video, client, fake_user):
    """Supprimer un match existant doit renvoyer 204 et déclencher le
    nettoyage de la vidéo associée dans Supabase Storage."""
    from api.main import app
    from api.deps import get_current_user

    fake_match = MagicMock(spec=Match)
    fake_match.video_storage_path = "user-123/video.mp4"

    app.dependency_overrides[get_current_user] = lambda: fake_user
    fake_db = make_fake_db({Match: fake_match})
    override_db(app, fake_db)

    response = client.delete("/matches/match-existant")

    assert response.status_code == 204
    mock_delete_video.assert_called_once_with("user-123/video.mp4")
    fake_db.delete.assert_called_once_with(fake_match)


@patch("api.routes_matches.delete_video", side_effect=Exception("Storage indisponible"))
def test_delete_match_still_succeeds_if_video_cleanup_fails(mock_delete_video, client, fake_user):
    """
    Si le nettoyage Storage échoue (réseau, fichier déjà absent...), la
    suppression du match en base ne doit PAS échouer — c'est un nettoyage
    'best-effort', documenté comme tel dans la route.
    """
    from api.main import app
    from api.deps import get_current_user

    fake_match = MagicMock(spec=Match)
    fake_match.video_storage_path = "user-123/video.mp4"

    app.dependency_overrides[get_current_user] = lambda: fake_user
    override_db(app, make_fake_db({Match: fake_match}))

    response = client.delete("/matches/match-existant")

    assert response.status_code == 204