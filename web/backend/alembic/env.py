import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Permet d'importer db.models depuis ce fichier, qui vit dans alembic/
# (un niveau plus bas que la racine backend/ où se trouvent nos packages).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Charge les variables d'environnement (.env), au même endroit que le reste
# du projet (backend/.env) — pour lire DATABASE_URL sans la dupliquer dans
# alembic.ini.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from db.models import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Injecte DATABASE_URL depuis .env dans la config Alembic, plutôt que de la
# dupliquer en dur dans alembic.ini.
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Nos modèles SQLAlchemy — nécessaire pour que `alembic revision --autogenerate`
# sache détecter les différences entre models.py et l'état réel de la base.
target_metadata = Base.metadata

# Nom de la table de suivi des migrations, DÉDIÉ à ce projet web. La base
# Supabase est partagée avec le projet iOS/Streamlit existant, qui a déjà sa
# propre table "alembic_version" — utiliser un nom différent ici évite tout
# conflit entre les deux historiques de migration, sans affecter les vraies
# tables de données (users, matches...), qui restent communes aux deux projets.
VERSION_TABLE = "alembic_version_web"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=VERSION_TABLE,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()