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

Les dépendances complètes sont déclarées dans `requirements.txt` et la
version du déploiement Railway dans le fichier `.python-version` à la racine.
L’export PDF nécessite aussi Chromium, installé après les paquets Python.

Depuis la racine du dépôt :

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m playwright install chromium
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
Le pipeline Core ML reste local. L’app peut envoyer ses résultats à
`POST /matches/sync` pour les retrouver côté web ; cet envoi n’inclut pas la vidéo.

## Routes principales

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/health` | Disponibilité HTTP |
| POST | `/auth/register` | Inscription |
| POST | `/auth/login` | Connexion |
| POST | `/auth/logout` | Suppression du cookie web |
| GET / PATCH | `/auth/me` | Profil et sport préféré |
| GET / POST | `/matches` | Bibliothèque et import vidéo |
| POST | `/matches/sync` | Enregistrement des analyses iOS |
| GET / DELETE | `/matches/{id}` | Détail et suppression |
| POST | `/matches/{id}/analyze` | Analyse vidéo |
| GET | `/matches/{id}/events` | Événements |
| POST | `/matches/{id}/coach-report` | Rapport de coaching |
| POST | `/coach/recommendations` | Coaching RAG à partir des séquences iOS |
| GET / POST | `/matches/{id}/chat` | Historique et chat persistants |
| GET | `/matches/{id}/export-pdf` | Rapport PDF via Chromium |
| GET / POST | `/training-plan` | Historique et génération de plans |

Les routes protégées acceptent le Bearer iOS ou le cookie HttpOnly web.
Le JWT reste présent dans les réponses de connexion pour les clients natifs.
Le frontend envoie les requêtes avec `credentials: "include"`.

Configurer `CORS_ORIGINS` (origines séparées par des virgules, sans `*`),
`AUTH_COOKIE_SECURE=true` en HTTPS, et `AUTH_COOKIE_SAMESITE` selon le déploiement.
En local, utiliser le même nom d’hôte pour le frontend et l’API (par exemple
`localhost` pour les deux). Si les sites frontend/API sont différents,
`SameSite=None` exige HTTPS ; certains navigateurs bloquent néanmoins les
cookies tiers. Préférer des sous-domaines du même site ou un proxy de même origine.
Les écritures par cookie contrôlent l’origine ; les appels natifs Bearer restent acceptés.

## Base de données

Depuis la racine :

```bash
python -m alembic -c backend/alembic.ini current
python -m alembic -c backend/alembic.ini upgrade head
```

Cette configuration reprend les anciennes révisions et ajoute `chat_messages`.
Elle fonctionne sur une base vide ou déjà suivie par cet historique. Pour
les autres cas, suivre [le guide des migrations](alembic/README) avant toute
commande. L’application ne déclenche aucune migration automatiquement.

## Modèles et connaissances

Les poids YOLO sont lus dans `training/models/exported/` à la racine.
`CV_WEIGHTS_DIR` peut sélectionner un autre dossier, de préférence absolu.
Les prompts et connaissances restent dans `backend/agents/` et les index RAG
gardent leur emplacement relatif lors du déplacement.

## Vérification

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -q
```

Les tests utilisent une base SQLite isolée ou des doubles de test ; ils ne
contactent ni Supabase ni Groq et ne téléchargent pas les modèles RAG.
Ils couvrent notamment la connexion cookie/Bearer, la synchronisation iOS,
la persistance du chat, les droits d’accès, les migrations et la préparation
du PDF. Le rendu Chromium et l’analyse vidéo réelle restent à vérifier sur
l’environnement déployé.
