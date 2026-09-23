"""
Crée les tables en base à partir des modèles SQLAlchemy.

Utile pour un démarrage local / une démo (SQLite) sans passer par Alembic.
En production, les migrations Alembic restent la référence.

Usage :
    python -m backend.api.init_db
"""
from backend.db.session import engine
from backend.db.models import Base


def main():
    Base.metadata.create_all(bind=engine)
    print("Tables créées :", ", ".join(Base.metadata.tables.keys()))


if __name__ == "__main__":
    main()
