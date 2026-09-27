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
2. `railway.json` (à la racine) force le builder **NIXPACKS** et pointe vers
   `nixpacks.toml`. Un `requirements.txt` racine (qui référence
   `backend/requirements.railway.txt`) garantit aussi la détection Python si
   Railway retombe sur son builder Railpack. Version allégée : sans
   torch / ultralytics / streamlit / opencv (inutiles à l'API — l'app mobile
   fait sa CV en local).
3. Le service démarre avec :
   `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`

> **Note technique** : les dépendances lourdes de la vision (cv2, torch,
> ultralytics) ne sont importées que si l'on lance une analyse vidéo *côté
> serveur* (`mark_match_ready`). Sur le déploiement API, ce chemin n'est jamais
> emprunté — l'app mobile analyse en local et pousse le résultat via
> `POST /matches/sync`. L'import est donc différé pour que l'API démarre sans
> ces paquets.

## 3. Variables d'environnement (Railway → Variables)

Copier ces clés (valeurs dans `.env.api.local`, **jamais** commitées) :

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | Postgres Supabase (pooler, port 6543) |
| `SECRET_KEY` | Signature des tokens JWT (identique côté web) |
| `SUPABASE_URL` | Projet Supabase (Storage vidéos) |
| `SUPABASE_KEY` | Clé publique Supabase |
| `SUPABASE_SERVICE_KEY` | Clé service Supabase (Storage) |
| `GROQ_API_KEY` | Coaching IA (optionnel — sans clé, mode dégradé) |

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

## 6. La base est déjà migrée

Le schéma Supabase est à jour (révision Alembic `56822ee323a9`, dernière).
Aucune migration à relancer. Pour une future évolution du schéma :

```bash
cd streamlit
DATABASE_URL="<url-supabase>" python -m alembic upgrade head
```

## Notes

- Le premier appel au coaching IA peut être lent (chargement du modèle
  d'embeddings RAG) — préchargé au démarrage du serveur (`main.py`).
- Railway peut mettre le service en veille sur le plan gratuit ; le plan
  hobby (~5 $/mois) le garde éveillé — recommandé pour une démo.
