"""
Upload de vidéos vers le bucket Supabase Storage "videos".

Chaque vidéo est rangée sous un préfixe par utilisateur (user_id/...),
ce qui permet plus tard de restreindre l'accès par des policies RLS
sur le bucket sans changer le code applicatif.

Utilise SUPABASE_SERVICE_KEY (clé service_role) plutôt que la clé publique :
Streamlit s'exécute entièrement côté serveur (contrairement à un front JS
dans le navigateur), donc .env n'est jamais exposé au client — c'est le
même modèle de confiance que la connexion Postgres directe (DATABASE_URL),
qui contourne déjà RLS pour les mêmes raisons.
"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

BUCKET_NAME = "videos"

# Limite réelle du plan gratuit Supabase (plafond global du projet, non
# contournable sans passer sur un plan payant) — vérifiée ici pour donner
# un message d'erreur clair plutôt qu'un échec réseau incompréhensible.
MAX_UPLOAD_SIZE_MB = 50
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

_client: Client | None = None


def get_supabase_client() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        # service_role, PAS la clé publique : nécessaire côté serveur pour
        # écrire dans Storage sans policy RLS explicite sur le bucket.
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SERVICE_KEY manquantes dans .env "
                "(clé 'secret'/service_role, PAS la clé publishable — voir "
                "Supabase → Settings → API Keys → Secret keys)"
            )
        _client = create_client(url, key)
    return _client


class VideoTooLargeError(Exception):
    """Levée quand la vidéo dépasse la limite du plan Supabase actuel."""
    pass


def upload_video(user_id: str, filename: str, file_bytes: bytes) -> str:
    """
    Upload une vidéo dans le bucket "videos", sous user_id/timestamp_filename.
    Retourne le chemin de stockage (à sauvegarder dans Match.video_storage_path).
    Lève VideoTooLargeError si le fichier dépasse la limite du plan.
    """
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise VideoTooLargeError(
            f"Vidéo trop volumineuse ({size_mb:.1f} Mo) — limite actuelle : "
            f"{MAX_UPLOAD_SIZE_MB} Mo (plan gratuit Supabase). "
            f"Essaie une séquence plus courte."
        )

    safe_filename = filename.replace(" ", "_")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    storage_path = f"{user_id}/{timestamp}_{safe_filename}"

    client = get_supabase_client()
    content_type = "video/mp4" if filename.lower().endswith(".mp4") else "video/quicktime"

    client.storage.from_(BUCKET_NAME).upload(
        storage_path,
        file_bytes,
        {"content-type": content_type},
    )

    return storage_path


def get_video_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Génère une URL signée temporaire pour lire la vidéo (le bucket est privé,
    donc pas d'URL publique directe). expires_in est en secondes.
    """
    client = get_supabase_client()
    result = client.storage.from_(BUCKET_NAME).create_signed_url(storage_path, expires_in)
    return result["signedURL"]