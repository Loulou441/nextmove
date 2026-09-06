# NextMove API (FastAPI)

Backend REST **partagé** entre l'application web (Streamlit) et l'application
iOS. Il n'introduit aucune logique nouvelle : c'est une fine couche HTTP au-dessus
du code déjà présent dans `src/auth/` et `src/db/`.

Concrètement, l'API et le web utilisent :
- la **même base de données** (`src/db/models.py`, `src/db/session.py`) ;
- la **même logique d'authentification** (`src/auth/service.py`, `security.py`) ;
- les **mêmes tokens JWT** (`src/auth/tokens.py`, signés avec `SECRET_KEY`).

Conséquence : un compte créé sur le web fonctionne tel quel dans l'app iOS, et
inversement. Les matchs enregistrés d'un côté sont visibles de l'autre.

## Endpoints

| Méthode | Chemin            | Auth | Rôle                                             |
|---------|-------------------|------|--------------------------------------------------|
| GET     | `/health`         | non  | Sonde de disponibilité                           |
| POST    | `/auth/register`  | non  | Créer un compte, renvoie un token + l'utilisateur|
| POST    | `/auth/login`     | non  | Se connecter, renvoie un token + l'utilisateur   |
| GET     | `/auth/me`        | oui  | Valider une session / récupérer l'utilisateur    |
| GET     | `/matches`        | oui  | Lister les matchs de l'utilisateur connecté      |

Authentification : en-tête `Authorization: Bearer <token>` (le token est
renvoyé par `/auth/register` et `/auth/login`).

Documentation interactive auto-générée : `http://localhost:8000/docs`.

## Lancer en local

Prérequis : Python 3.10+ (le code utilise la syntaxe `str | None`).

```bash
python3.11 -m venv .venv_api
source .venv_api/bin/activate
pip install fastapi uvicorn "pydantic[email]" python-multipart PyJWT bcrypt \
            "SQLAlchemy>=2.0" python-dotenv
```

Renseigner `DATABASE_URL` et `SECRET_KEY` dans le `.env` du projet.
Pour une démo locale sans Postgres, SQLite suffit :

```env
DATABASE_URL=sqlite:///./nextmove_demo.db
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">
```

Créer les tables puis démarrer :

```bash
python -m src.api.init_db
uvicorn src.api.main:app --reload --port 8000
```

> En production, la base est PostgreSQL (Supabase) et les migrations sont
> gérées par Alembic ; `init_db` est un raccourci réservé au local/démo.

## Test rapide (curl)

```bash
# inscription
curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"demo@nextmove.app","password":"demo1234","preferred_sport":"padel"}'

# connexion
curl -X POST localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"email":"demo@nextmove.app","password":"demo1234"}'

# route protégée (remplacer <TOKEN>)
curl localhost:8000/matches -H "Authorization: Bearer <TOKEN>"
```

## Côté iOS

Le client Swift `NextMoveAPI` (voir `nextmove/Services/NextMoveAPI.swift` sur la
branche iOS) appelle ces endpoints. La connexion iOS est **réelle** : elle passe
par `/auth/login`, stocke le token et l'envoie en Bearer sur les requêtes
suivantes.
