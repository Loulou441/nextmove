"""Migrations de l'API commune, avec la même configuration que le serveur."""
import os
from alembic import context
from sqlalchemy import create_engine, pool
from backend import config as backend_config  # charge backend/.env puis .env
from backend.db.models import Base

url = os.environ.get("DATABASE_URL")
if not url:
    raise RuntimeError("DATABASE_URL manquante")

if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
