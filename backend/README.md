# NextMove — API commune React et iOS

Ce dossier héberge le serveur FastAPI, les services d’analyse vidéo et les agents
de coaching. Streamlit conserve ses services Python et son déploiement propre.

## Migration depuis l’organisation précédente

Le serveur a été déplacé depuis `web/backend/` vers `backend/`. L’ancienne API
`streamlit/src/api/` a été retirée. Les routes et le format JWT utilisés par iOS
sont conservés, mais l’API doit être lancée ou déployée séparément des interfaces.

Les fichiers locaux ignorés par Git ne sont pas déplacés par cette modification :
copier son ancien `web/backend/.env` vers `backend/.env` et recréer si nécessaire
l’environnement virtuel. Réutiliser `DATABASE_URL` et `SECRET_KEY` pour conserver
les comptes et accepter les tokens existants. Ne pas écraser un `.env` existant.

## Installation et configuration

Depuis la racine du dépôt :

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Créer `backend/.env` à partir de `backend/.env.example`. Il contient la connexion
PostgreSQL, `SECRET_KEY`, les accès Supabase et `GROQ_API_KEY`.
Le bucket Supabase privé attendu est `videos`.
Ne jamais versionner ces valeurs ou les exposer dans le frontend.

Les variables du processus sont prioritaires, puis `backend/.env`, puis le
`.env` racine conservé pour Streamlit. Les chemins sont calculés depuis les
fichiers Python, indépendamment du dossier courant.

## Lancement

Depuis la racine, avec l’environnement Python activé :

```bash
python -m uvicorn backend.api.main:app --reload --port 8000
```

Depuis un autre dossier, utiliser `--app-dir /chemin/absolu/vers/le/depot`.
Ne plus utiliser `api.main:app` ou `src.api.main:app`.

- Sonde HTTP : http://localhost:8000/health
- Contrats interactifs : http://localhost:8000/docs

Le premier démarrage peut nécessiter le téléchargement des modèles d’embeddings
et la préparation des connaissances RAG. `/health` ne valide pas les services externes.

## Clients

- React : `NEXT_PUBLIC_API_URL` dans `web/frontend/.env.local`.
- iOS : `NEXTMOVE_API_URL` dans le schéma Xcode ou Info.plist.
- Valeur locale commune : `http://localhost:8000`.

Pour un iPhone physique, choisir une URL accessible depuis le téléphone.
La bibliothèque iOS et le pipeline Core ML restent locaux ; aucune synchronisation
supplémentaire n’est introduite par ce déplacement.

## Routes principales

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/health` | Disponibilité HTTP |
| POST | `/auth/register` | Inscription |
| POST | `/auth/login` | Connexion |
| GET / PATCH | `/auth/me` | Profil et sport préféré |
| GET / POST | `/matches` | Bibliothèque et import vidéo |
| GET / DELETE | `/matches/{id}` | Détail et suppression |
| POST | `/matches/{id}/analyze` | Analyse vidéo |
| GET | `/matches/{id}/events` | Événements |
| POST | `/matches/{id}/coach-report` | Rapport de coaching |
| POST | `/matches/{id}/chat` | Chat |
| GET / POST | `/training-plan` | Historique et génération de plans |

Les routes protégées attendent `Authorization: Bearer <token>`.

## Base de données

Les migrations existantes restent dans `streamlit/alembic/` et ne sont pas
dupliquées. Depuis la racine, pour appliquer ces migrations avec la configuration
du backend :

```bash
python - <<'PY'
import subprocess
import sys
from backend.config import REPO_ROOT

subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=REPO_ROOT / "streamlit",
    check=True,
)
PY
```

Vérifier la base ciblée avant d’appliquer les migrations. Pour une base de test
vide uniquement, `python -m backend.api.init_db` crée les tables des modèles ;
cette commande ne remplace pas les migrations et ne met pas à niveau un schéma existant.

## Modèles et connaissances

Les poids YOLO sont lus dans `training/models/exported/` à la racine.
`CV_WEIGHTS_DIR` peut sélectionner un autre dossier, de préférence absolu.
Les prompts et connaissances restent dans `backend/agents/` et les index RAG
gardent leur emplacement relatif lors du déplacement.

## Vérification

Tester l’inscription, la connexion, `/auth/me` et `/matches` depuis les deux
clients, puis un import, une analyse et le coaching côté web.
Les paramètres CORS actuels sont destinés au développement ; configurer les
origines autorisées et HTTPS avant une exposition en production.
