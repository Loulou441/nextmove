# Déploiement de NextMove (Vercel + AWS EC2)

Ce guide déploie l'API FastAPI dans un conteneur Docker sur une instance AWS EC2,
et l'interface web sur Vercel. L'app mobile et le web partagent les mêmes comptes
et les mêmes données grâce à une base Supabase unique.

## Architecture

```
App mobile (Core ML) ─┐
                      ├─► API FastAPI (Docker sur AWS EC2, HTTPS) ─┬─► Supabase Postgres
App web (Vercel)     ─┘                                            ├─► Supabase Storage (vidéos)
                                                                   ├─► Groq (coaching IA)
                                                                   └─► Resend (emails de vérification)
```

Un seul compte, une seule base : une analyse faite sur mobile est visible sur le
web après connexion (via `POST /matches/sync`). L'analyse vidéo web est faite côté
serveur (YOLO) dans le conteneur.

> Railway n'est plus utilisé. Les fichiers `railway.json`, `nixpacks.toml`, `Procfile`
> et `backend/requirements.railway.txt` sont conservés pour mémoire et ne servent plus
> au déploiement.

## 1. Prérequis

- Une instance AWS EC2 avec Docker installé : type **[à compléter]**, au moins 4 Go de
  RAM et 20 à 30 Go de disque (l'image contient PyTorch, Chromium et le modèle
  d'embeddings ; vérifier sa taille réelle après le build).
- Un nom de domaine pour l'API, par exemple `api.nextmoveapp.lol` **[à confirmer]**,
  dont l'enregistrement DNS pointe vers l'adresse IP de l'instance.
- Le projet Supabase existant (base et Storage, bucket privé `videos`).
- Un compte Resend avec le domaine `nextmoveapp.lol` vérifié (expéditeur
  `noreply@nextmoveapp.lol`).
- Un compte Vercel relié au dépôt GitHub.

## 2. Construire l'image Docker

Depuis la racine du dépôt (le contexte de build est la racine, pas `backend/`) :

```bash
docker build -t nextmove-api .
```

Le `Dockerfile` installe PyTorch (CPU), les dépendances de `backend/requirements.txt`,
le modèle d'embeddings et Chromium (export PDF), puis copie `backend/` et les poids
YOLO de `training/models/exported/` aux mêmes emplacements que dans le dépôt.
Le service démarre avec `backend/start.sh` :
`python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000`.

Pour tester l'image en local :

```bash
docker run --rm -p 8000:8000 --env-file backend/.env nextmove-api
```

puis ouvrir http://localhost:8000/docs.

L'image peut être construite directement sur l'instance (`git clone`, `git checkout`,
`docker build`) ou construite ailleurs puis publiée dans un registre (Docker Hub,
GitHub Container Registry, AWS ECR) et récupérée sur l'instance avec `docker pull`.

## 3. Configurer l'instance EC2

Groupe de sécurité :

| Port | Ouverture |
|---|---|
| 22 | SSH, restreint à vos adresses IP |
| 80 et 443 | Public (HTTP pour le certificat, HTTPS pour l'API) |
| 8000 | **Fermé** à l'extérieur : seul le reverse proxy y accède |

## 4. Variables d'environnement

Créer un fichier `.env` **sur le serveur** (jamais commité), à partir de
`backend/.env.example` :

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | Postgres Supabase (pooler, port 6543) |
| `SECRET_KEY` | Signature des tokens JWT (identique à l'ancien déploiement pour garder les sessions et les comptes) |
| `SUPABASE_URL` | Projet Supabase (Storage vidéos) |
| `SUPABASE_KEY` | Clé publique Supabase |
| `SUPABASE_SERVICE_KEY` | Clé service Supabase (Storage) |
| `GROQ_API_KEY` | Coaching IA |
| `RESEND_API_KEY` | Envoi des emails de vérification et de réinitialisation de mot de passe |
| `CORS_ORIGINS` | URL exacte du frontend (par exemple `https://app.nextmoveapp.lol`), séparées par des virgules, sans `*` |
| `AUTH_COOKIE_SECURE` | `true` (HTTPS) |
| `AUTH_COOKIE_SAMESITE` | `lax` si le frontend et l'API sont sur le même site (sous-domaines de `nextmoveapp.lol`) ; `none` s'ils sont sur des sites différents (par exemple `*.vercel.app` et le domaine de l'API) |
| `CV_WEIGHTS_DIR` | Facultatif : dossier des poids YOLO (par défaut `training/models/exported/` dans l'image) |

> **Cookies.** Avec un frontend sur `*.vercel.app` et une API sur un autre domaine,
> le cookie est « tiers » : certains navigateurs (Safari, Chrome avec blocage des
> cookies tiers) le bloquent même avec `SameSite=None`. Pour une connexion fiable,
> servir le frontend et l'API comme sous-domaines du même site (par exemple
> `app.nextmoveapp.lol` pour Vercel et `api.nextmoveapp.lol` pour EC2) et utiliser
> `AUTH_COOKIE_SAMESITE=lax`.

## 5. HTTPS

Placer un reverse proxy devant l'API. Avec Caddy (certificat Let's Encrypt automatique),
le fichier `/etc/caddy/Caddyfile` suffit :

```
api.nextmoveapp.lol {
    reverse_proxy 127.0.0.1:8000
}
```

Avec nginx, prévoir `client_max_body_size 60m;` : l'API accepte des vidéos jusqu'à
50 Mo (`MAX_UPLOAD_SIZE_MB` dans `backend/services/video_storage.py`).

## 6. Migrer la base

Avant de servir cette version, vérifier la base cible et **sauvegarder ses données**.
Depuis l'image (ou depuis la racine du dépôt avec l'environnement Python du backend) :

```bash
docker run --rm --env-file .env nextmove-api \
  python -m alembic -c backend/alembic.ini current
docker run --rm --env-file .env nextmove-api \
  python -m alembic -c backend/alembic.ini upgrade head
```

La chaîne de révisions est : `56822ee323a9` → `7b9e20260927` (chat persistant) →
`4b5d2fafb134` (vérification d'email : colonne `users.email_verified`, table
`verification_codes`). Ne pas supposer que la base est à jour.

**Base déjà utilisée par l'ancien déploiement de `nextmove_web`.** Si `current` affiche
une révision de l'historique indépendant de `nextmove_web` (par exemple `6c2d5b477eae`),
ou si les tables `chat_messages` / `verification_codes` ou la colonne `users.email_verified`
existent déjà, ne lancez pas `upgrade head` sans comparer le schéma réel aux migrations.
Voir [les cas particuliers](alembic/README).

Aucune migration n'est exécutée automatiquement par le service.

## 7. Lancer l'API

```bash
docker run -d --name nextmove-api --restart unless-stopped \
  -p 127.0.0.1:8000:8000 --env-file .env nextmove-api
```

`--restart unless-stopped` relance l'API après un redémarrage de l'instance.
Journaux : `docker logs -f nextmove-api`.

Tester : `https://api.nextmoveapp.lol/health` doit renvoyer `{"status":"ok"}`
(`/health` ne vérifie pas la base, Groq, Storage, Resend ni Chromium).
Documentation interactive : `https://api.nextmoveapp.lol/docs`.

Mise à jour : récupérer la nouvelle version du code, reconstruire l'image,
appliquer les migrations (étape 6), puis remplacer le conteneur
(`docker rm -f nextmove-api`, puis relancer la commande ci-dessus).

## 8. Déployer le frontend sur Vercel

1. Vercel → **Add New → Project** → importer `Loulou441/nextmove`.
2. **Root Directory** : `web/frontend` (Framework : Next.js, détecté automatiquement).
3. **Environment Variables** : `NEXT_PUBLIC_API_URL` = URL HTTPS de l'API
   (par exemple `https://api.nextmoveapp.lol`). Cette variable est lue **à la
   compilation** : après toute modification, redéployer.
4. Branche de production : `main` (les autres branches produisent des déploiements
   de prévisualisation).
5. Domaine personnalisé : ajouter `app.nextmoveapp.lol` **[à confirmer]** et reporter
   cette URL dans `CORS_ORIGINS` côté API.

## 9. Pointer l'app mobile vers l'API

Dans `ios/nextmove/Info.plist`, renseigner la clé `NEXTMOVE_API_URL` :

```xml
<key>NEXTMOVE_API_URL</key>
<string>https://api.nextmoveapp.lol</string>
```

En HTTPS, aucune exception ATS n'est nécessaire (le bloc `NSAppTransportSecurity`
ne garde que `NSAllowsLocalNetworking` pour le développement en simulateur).
Recompiler l'application après modification.

## 10. Vérifier le déploiement

Avec un compte de test :

1. Inscription : l'email de vérification arrive depuis `noreply@nextmoveapp.lol`.
2. Connexion web : le cookie `access_token` est posé (HttpOnly, `Secure`, `SameSite`
   attendu) et la session persiste après rechargement.
3. Import d'une vidéo, analyse (état jusqu'à `ready`), détail du match.
4. Chat du coach, rechargement de la page (la conversation est conservée).
5. Export PDF.
6. Connexion et synchronisation depuis l'app iOS, puis consultation sur le web.

`/health` seul ne prouve pas que la base, Groq, Storage, Resend ou Chromium fonctionnent.
Le premier appel au coaching peut être lent pendant le chargement des embeddings.

## Dépannage

| Symptôme | Vérification |
|---|---|
| Le web affiche « Failed to fetch » | `NEXT_PUBLIC_API_URL` (redéployer après modification), HTTPS de l'API, `CORS_ORIGINS` |
| Connexion qui ne persiste pas | `AUTH_COOKIE_SECURE=true`, `AUTH_COOKIE_SAMESITE` adapté, frontend et API sur le même site si possible |
| Inscription en erreur 502 | `RESEND_API_KEY` présente et domaine vérifié dans Resend |
| Import de vidéo refusé | Taille de la vidéo (limite de 50 Mo), `client_max_body_size` du proxy, bucket `videos` |
| Analyse en échec | Poids dans `training/models/exported/` ou `CV_WEIGHTS_DIR`, mémoire de l'instance, `docker logs` |
| Export PDF indisponible (503) | Chromium installé dans l'image, mémoire disponible |
| Erreur SQL ou de révision | Étape 6, sauvegarde et état de `alembic current` |
