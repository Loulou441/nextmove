# Déploiement de NextMove (Vercel + AWS EC2)

Ce guide déploie l'API FastAPI dans un conteneur Docker sur une instance AWS EC2
(`m7i-flex.large`), et l'interface web sur Vercel. L'app mobile et le web partagent les mêmes comptes
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

> Railway n'est plus utilisé : ses fichiers de configuration (`railway.json`,
> `nixpacks.toml`, `Procfile`) ont été supprimés du dépôt.

## 1. Prérequis

- Une instance AWS EC2 `m7i-flex.large` (2 vCPU, 8 Go de RAM), sous Ubuntu Server LTS,
  avec un volume EBS d'au moins 30 Go (l'image contient PyTorch, Chromium et le modèle
  d'embeddings ; vérifier sa taille réelle après le build) et une adresse IP élastique.
  Compter 8 Go de RAM au minimum : l'analyse vidéo (YOLO) et l'export PDF (Chromium)
  sont gourmands, et 4 Go risquent de ne pas suffire en cas d'usages simultanés.
- Un nom de domaine pour l'API, par exemple `api.nextmoveapp.lol`,
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

**Création.** Console AWS → EC2 → *Launch instance* :

| Paramètre | Valeur |
|---|---|
| Type | `m7i-flex.large` (2 vCPU, 8 Go de RAM) |
| Système | Ubuntu Server LTS (les commandes ci-dessous supposent Ubuntu ou Debian) |
| Stockage | Volume EBS gp3 de 30 Go minimum |
| Clé SSH | Une paire de clés propre au projet, conservée hors du dépôt |
| Région | **[à compléter]**, la même que celle utilisée pour les estimations de coûts |

**Adresse IP élastique.** Associer une *Elastic IP* à l'instance (EC2 → *Elastic IPs*) :
sans elle, l'IP publique change à chaque arrêt de l'instance et l'enregistrement DNS
devient faux. Créer ensuite l'enregistrement DNS `A` de `api.nextmoveapp.lol` vers
cette adresse.

**Groupe de sécurité :**

| Port | Ouverture |
|---|---|
| 22 | SSH, restreint à vos adresses IP |
| 80 et 443 | Public (HTTP pour le certificat, HTTPS pour l'API) |
| 8000 | **Fermé** à l'extérieur : seul le reverse proxy y accède |

**Installation de Docker et de Git** (connexion SSH à l'instance) :

```bash
sudo apt-get update
sudo apt-get install -y docker.io git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # puis se déconnecter et se reconnecter
```

Le dépôt peut alors être cloné sur l'instance (`git clone https://github.com/Loulou441/nextmove.git`)
pour construire l'image (étape 2). Sur Amazon Linux, les commandes d'installation
diffèrent (`dnf` au lieu d'`apt-get`).

## Coûts indicatifs

| Poste | Coût |
|---|---|
| EC2 `m7i-flex.large`, tarif à la demande | 0,1017 $ de l'heure, soit environ 74 $ par mois en usage continu (730 h) |
| Volume EBS gp3 (30 Go) | À ajouter ; voir la grille de tarifs de la région |
| Adresse IPv4 publique | À ajouter ; AWS facture désormais les IPv4 publiques |
| Transfert de données sortant | À ajouter ; au-delà du quota gratuit d'AWS |

Le tarif horaire est celui d'une instance Linux à la demande ; il varie selon la région.
Arrêter l'instance (et non la résilier) interrompt la facturation de l'instance, mais
pas celle du volume EBS ni de l'IP élastique.

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
> `AUTH_COOKIE_SAMESITE=lax`. Tant que le frontend reste sur son adresse
> `*.vercel.app`, utiliser `AUTH_COOKIE_SAMESITE=none` et tester la connexion sous Safari.

## 5. HTTPS

Placer un reverse proxy devant l'API. Avec Caddy (certificat Let's Encrypt automatique),
installer Caddy sur l'instance :

```bash
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update && sudo apt-get install -y caddy
```

puis écrire le fichier `/etc/caddy/Caddyfile` :

```
api.nextmoveapp.lol {
    reverse_proxy 127.0.0.1:8000
}
```

et recharger la configuration avec `sudo systemctl reload caddy`. Le DNS de
`api.nextmoveapp.lol` doit déjà pointer vers l'IP élastique, et les ports 80 et 443
doivent être ouverts, sans quoi Let's Encrypt ne peut pas délivrer le certificat.

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
`verification_codes`) → `a7c1e9d2b3f4` (joueurs détectés : colonnes `matches.players` et
`matches.selected_player_index`). Ne pas supposer que la base est à jour.

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
5. Domaine du frontend : ajouter `app.nextmoveapp.lol` **[à confirmer]** pour que le
   frontend et l'API soient sur le même site (voir la section Cookies) et reporter cette
   URL dans `CORS_ORIGINS` côté API. Si le frontend reste sur son adresse `*.vercel.app`
   (par exemple `https://nextmove-gold.vercel.app`), reporter cette adresse à la place.

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
| Analyse en échec | Poids dans `training/models/exported/` ou `CV_WEIGHTS_DIR`, mémoire de l'instance (`free -h`, `docker stats`), `docker logs` |
| Le certificat HTTPS n'est pas délivré | DNS de l'API vers l'IP élastique, ports 80 et 443 ouverts dans le groupe de sécurité, `sudo journalctl -u caddy` |
| L'API est injoignable après un redémarrage | Adresse IP élastique associée, conteneur lancé avec `--restart unless-stopped`, `sudo systemctl status docker caddy` |
| Export PDF indisponible (503) | Chromium installé dans l'image, mémoire disponible |
| Erreur SQL ou de révision | Étape 6, sauvegarde et état de `alembic current` |
