"""
Configuration du moteur SQLAlchemy et des sessions de base de données.
"""

import os
from pathlib import Path
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[3]

# Charge les variables d'environnement depuis .env ET .env.api.local (secrets API :
# DATABASE_URL, SECRET_KEY). On ne surcharge pas les variables déjà définies dans
# l'environnement, donc un export explicite reste prioritaire.
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.api.local")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL manquante — définis-la dans .env ou .env.api.local "
        "(voir .env.example pour le format attendu)."
    )


def _resolve_sqlite_path(url: str) -> str:
    """Ancre un chemin SQLite relatif à la racine du projet.

    `sqlite:///./nextmove_demo.db` dépend sinon du répertoire de lancement
    d'uvicorn : lancé ailleurs qu'à la racine, il crée une base VIDE au mauvais
    endroit. On réécrit donc le chemin relatif en chemin absolu basé sur ROOT
    pour que la vraie base soit toujours trouvée.
    """
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url
    path_part = url[len(prefix):]
    # ':memory:' ou chemin déjà absolu (sqlite:////abs/path) -> ne rien changer
    if path_part.startswith(":memory:") or path_part.startswith("/"):
        return url
    relative = path_part[2:] if path_part.startswith("./") else path_part
    return f"{prefix}{(ROOT / relative).resolve()}"


DATABASE_URL = _resolve_sqlite_path(DATABASE_URL)

# pool_pre_ping évite les erreurs de connexion "stale" (utile avec le pooler Supabase
# qui peut fermer des connexions inactives).
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_db_session():
    """
    Context manager pour une session DB avec commit/rollback automatique.

    Usage :
        with get_db_session() as db:
            db.add(some_object)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()