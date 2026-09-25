"""
Tests unitaires pour services/video_storage.py — le client Supabase est
mocké partout : aucun de ces tests ne doit toucher au vrai réseau/bucket.
"""
from unittest.mock import MagicMock, patch

import pytest

from services.video_storage import (
    upload_video, delete_video, VideoTooLargeError,
    MAX_UPLOAD_SIZE_BYTES,
)


def test_upload_video_too_large_raises_before_any_network_call():
    """
    Un fichier dépassant la limite doit être rejeté immédiatement, sans
    jamais tenter de contacter Supabase (vérifié en mockant le client et en
    s'assurant qu'il n'est pas appelé).
    """
    oversized_bytes = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)

    with patch("services.video_storage.get_supabase_client") as mock_get_client:
        with pytest.raises(VideoTooLargeError):
            upload_video("user-123", "match.mp4", oversized_bytes)
        mock_get_client.assert_not_called()


def test_upload_video_error_message_mentions_size_limit():
    """Le message d'erreur doit être compréhensible (mentionne la limite en Mo)."""
    oversized_bytes = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)

    with patch("services.video_storage.get_supabase_client"):
        with pytest.raises(VideoTooLargeError, match="50 Mo"):
            upload_video("user-123", "match.mp4", oversized_bytes)


@patch("services.video_storage.get_supabase_client")
def test_upload_video_success_returns_storage_path_with_user_prefix(mock_get_client):
    """Un upload valide doit renvoyer un chemin préfixé par l'id utilisateur."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    storage_path = upload_video("user-123", "match.mp4", b"contenu-video")

    assert storage_path.startswith("user-123/")
    assert storage_path.endswith("_match.mp4")
    mock_client.storage.from_.assert_called_once_with("videos")


@patch("services.video_storage.get_supabase_client")
def test_upload_video_replaces_spaces_in_filename(mock_get_client):
    """Les espaces dans le nom de fichier doivent être remplacés (évite des
    soucis d'URL/chemins mal encodés côté Supabase)."""
    mock_get_client.return_value = MagicMock()

    storage_path = upload_video("user-123", "mon match du samedi.mp4", b"contenu")

    assert " " not in storage_path
    assert "mon_match_du_samedi.mp4" in storage_path


@patch("services.video_storage.get_supabase_client")
def test_upload_video_sets_correct_content_type_for_mov(mock_get_client):
    """Un fichier .mov doit être uploadé avec le content-type QuickTime, pas mp4."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    upload_video("user-123", "match.mov", b"contenu")

    _, _, options = mock_client.storage.from_.return_value.upload.call_args[0]
    assert options["content-type"] == "video/quicktime"


def test_delete_video_with_empty_path_does_nothing():
    """Un chemin vide (match jamais réellement uploadé) ne doit pas planter,
    ni tenter d'appeler Supabase."""
    with patch("services.video_storage.get_supabase_client") as mock_get_client:
        delete_video("")
        mock_get_client.assert_not_called()


def test_delete_video_with_none_does_nothing():
    """Idem avec None au lieu d'une chaîne vide."""
    with patch("services.video_storage.get_supabase_client") as mock_get_client:
        delete_video(None)
        mock_get_client.assert_not_called()


@patch("services.video_storage.get_supabase_client")
def test_delete_video_calls_remove_with_correct_path(mock_get_client):
    """Un chemin valide doit être transmis tel quel à l'appel remove()."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    delete_video("user-123/20260908_match.mp4")

    mock_client.storage.from_.return_value.remove.assert_called_once_with(
        ["user-123/20260908_match.mp4"]
    )