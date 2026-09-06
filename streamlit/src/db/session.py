"""
Configuration du moteur SQLAlchemy et des sessions de base de données.
"""

import os
from pathlib import Path
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL manquante dans .env — voir .env.example pour le format attendu."
    )

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