# Déploiement du backend NextMove (Railway)

Ce guide déploie l'API FastAPI sur Railway avec Supabase Postgres, pour que
l'app mobile et le web partagent les mêmes comptes et les mêmes données.

## Architecture

```
App mobile (Core ML) ─┐
                      ├─► API FastAPI (Railway, HTTPS) ─► Supabase Postgres
App web (React)      ─┘                                └─► Supabase Storage (vidéos)
```

Un seul compte, une seule base : une analyse faite sur mobile est visible
sur le web après connexion (via POST /matches/sync).

## 1. Prérequis

- Un compte Railway (railway.app) — connexion via GitHub.
- Le projet Supabase existant (base + Storage) — credentials fournis par Ayoub.

## 2. Créer le service sur Railway

1. Railway → **New Project** → **Deploy from GitHub repo** → choisir `Loulou441/nextmove`.
2. `railway.json` utilise Nixpacks avec `nixpacks.toml`. Les dépendances API
   sont installées depuis `requirements.txt` à la racine ; le build installe
   aussi Chromium et ses dépendances système pour l’export PDF.
3. Le service démarre avec :
   `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`

Cette configuration n’installe pas OpenCV ni Ultralytics. Elle permet de
recevoir les analyses mobiles, mais ne suffit pas pour analyser les vidéos
web côté serveur. Pour ce parcours, installer les dépendances complètes de
`backend/requirements.txt` et disposer des poids YOLO et des ressources
nécessaires. Les embeddings RAG utilisent sentence-transformers et peuvent
installer PyTorch même dans la configuration API.

## 3. Variables d'environnement (Railway → Variables)

Copier ces clés (valeurs dans `.env.api.local`, **jamais** commitées) :

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | Postgres Supabase (pooler, port 6543) |
| `SECRET_KEY` | Signature des tokens JWT (identique côté web) |
| `SUPABASE_URL` | Projet Supabase (Storage vidéos) |
| `SUPABASE_KEY` | Clé publique Supabase |
| `SUPABASE_SERVICE_KEY` | Clé service Supabase (Storage) |
| `GROQ_API_KEY` | Coaching IA |
| `CORS_ORIGINS` | Origines exactes du frontend, séparées par des virgules |
| `AUTH_COOKIE_SECURE` | `true` en production HTTPS |
| `AUTH_COOKIE_SAMESITE` | `lax` pour le même site ; `none` si sites différents |

> `DATABASE_URL` et `SECRET_KEY` doivent être **identiques** à ceux du web
> pour que les comptes et les tokens soient interopérables.

## 4. Récupérer l'URL publique

Railway → Settings → **Generate Domain**. On obtient une URL du type :
`https://nextmove-api-production.up.railway.app`

Tester : `https://<url>/health` doit renvoyer `{"status":"ok"}`.
Docs interactives : `https://<url>/docs`.

## 5. Pointer l'app mobile vers l'URL de prod

Dans `ios/nextmove/Info.plist`, renseigner la clé `NEXTMOVE_API_URL` :

```xml
<key>NEXTMOVE_API_URL</key>
<string>https://nextmove-api-production.up.railway.app</string>
```

En HTTPS, aucune exception ATS n'est nécessaire (le bloc `NSAppTransportSecurity`
ne garde que `NSAllowsLocalNetworking` pour le dev en simulateur).

## 6. Migrer la base pour le chat persistant

Avant de servir cette version, vérifier la base cible et sauvegarder ses données :

```bash
python -m alembic -c backend/alembic.ini current
python -m alembic -c backend/alembic.ini upgrade head
```

La nouvelle révision est `7b9e20260927`, après `56822ee323a9`. Ne pas supposer
que la base est déjà à jour. Voir [les cas particuliers](alembic/README) si
elle a été créée avec `init_db` ou depuis l’historique indépendant de `nextmove_web`.
Aucune commande de migration n’est exécutée automatiquement par le service.

## 7. Vérifier le déploiement

Vérifier la connexion web et iOS, la synchronisation mobile, le chat après
rechargement et le téléchargement d’un PDF. `/health` seul ne prouve pas que
la base, Groq, Storage ou Chromium fonctionnent.

Le premier appel au coaching peut être lent pendant le chargement des embeddings.
Pour les cookies, préférer frontend et API sur le même site ; les cookies
inter-sites peuvent être bloqués par le navigateur même avec `SameSite=None`.
