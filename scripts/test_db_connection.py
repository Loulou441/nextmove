"""
Script de vérification de la connexion à la base de données Supabase/Postgres.

Usage :
    python scripts/test_db_connection.py

Vérifie, dans l'ordre :
1. Que les variables d'environnement nécessaires sont bien présentes dans .env
2. Que la connexion Postgres (via DATABASE_URL) fonctionne
3. Que le client Supabase (via SUPABASE_URL / SUPABASE_KEY) répond
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

REQUIRED_VARS = ["DATABASE_URL", "SUPABASE_URL", "SUPABASE_KEY"]


def check_env_vars() -> bool:
    print("── 1. Vérification des variables d'environnement ──")
    missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
    if missing:
        print(f"❌ Variables manquantes dans .env : {', '.join(missing)}")
        return False
    for v in REQUIRED_VARS:
        val = os.environ[v]
        masked = val[:15] + "..." if len(val) > 15 else val
        print(f"✅ {v} trouvée ({masked})")
    return True


def check_postgres_connection() -> bool:
    print("\n── 2. Test de connexion Postgres (SQLAlchemy) ──")
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("❌ SQLAlchemy n'est pas installé (pip install sqlalchemy)")
        return False

    database_url = os.environ["DATABASE_URL"]
    try:
        engine = create_engine(database_url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Connexion Postgres réussie")
            print(f"   Version : {version}")
        return True
    except Exception as e:
        print(f"❌ Échec de connexion Postgres : {e}")
        print("   → Si l'erreur mentionne un timeout, essaie 'Session pooler' au lieu")
        print("     de 'Transaction pooler' dans Supabase (Connect → Direct connection),")
        print("     c'est souvent un souci de compatibilité IPv4/IPv6.")
        return False


def check_supabase_client() -> bool:
    print("\n── 3. Test du client Supabase (Storage/API) ──")
    try:
        from supabase import create_client
    except ImportError:
        print("❌ Le package supabase n'est pas installé (pip install supabase)")
        return False

    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    try:
        client = create_client(url, key)
        # Un simple appel léger pour vérifier que le client est bien configuré
        buckets = client.storage.list_buckets()
        print(f"✅ Client Supabase initialisé avec succès")
        print(f"   Buckets Storage existants : {len(buckets)}")
        return True
    except Exception as e:
        print(f"❌ Échec d'initialisation du client Supabase : {e}")
        return False


if __name__ == "__main__":
    ok_env = check_env_vars()
    if not ok_env:
        print("\n⚠️  Corrige d'abord ton .env avant de continuer.")
        sys.exit(1)

    ok_pg = check_postgres_connection()
    ok_sb = check_supabase_client()

    print("\n── Résumé ──")
    if ok_pg and ok_sb:
        print("🎉 Tout fonctionne, on peut passer au schéma de BDD.")
        sys.exit(0)
    else:
        print("⚠️  Au moins un test a échoué, corrige avant de continuer.")
        sys.exit(1)