# NextMove Web

La solution web NextMove associe une interface React / Next.js à une API
FastAPI. Elle permet d’importer des vidéos, de lancer leur analyse et de
consulter les résultats et recommandations de coaching.

## Organisation

| Dossier | Rôle |
|---|---|
| `frontend/app/` | Pages et layouts Next.js |
| `frontend/components/` | Composants d’interface |
| `frontend/lib/api.ts` | Client HTTP de l’API |
| `frontend/lib/auth-context.tsx` | État d’authentification |
| `frontend/public/` | Ressources statiques |
| `backend/api/` | Routes FastAPI et schémas HTTP |
| `backend/auth/` | Services d’authentification et tokens |
| `backend/db/` | Modèles SQLAlchemy et connexion SQL |
| `backend/services/` | Analyse vidéo, stockage et persistance |
| `backend/agents/` | Coaching, modération et recherche documentaire |

## Prérequis

- Python compatible avec `backend/requirements.txt`.
- Node.js compatible avec la version de Next.js déclarée dans
  `frontend/package.json`, et npm.
- Une base PostgreSQL avec le schéma NextMove.
- Un projet Supabase Storage avec un bucket privé nommé `videos`.
- Une clé Groq pour le coaching et le chat.
- Les modèles YOLO dans `../training/models/exported/`.

Le frontend et le backend sont deux processus distincts.

## 1. Installer le backend

Depuis la racine du dépôt :

```bash
cd web/backend

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt
```

Sous PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
```

L’installation des dépendances de vision et de recherche documentaire
peut prendre du temps.

## 2. Configurer le backend

Créer `web/backend/.env` :

```dotenv
DATABASE_URL=postgresql://utilisateur:mot_de_passe@hote:5432/base
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_SERVICE_KEY=votre_cle_serveur
SECRET_KEY=votre_secret_jwt
GROQ_API_KEY=votre_cle_groq
```

Pour générer un secret JWT :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Les guillemets sont facultatifs pour les valeurs simples.
Si le mot de passe PostgreSQL contient des caractères réservés d’URL,
les encoder dans `DATABASE_URL`.

Ne pas placer les clés serveur dans le frontend ni dans une variable
préfixée par `NEXT_PUBLIC_`.

### Utiliser une base existante

La base peut être celle de Streamlit si son schéma est initialisé.

Dans ce cas, les créations et suppressions de matchs affectent les mêmes
données. Utiliser un compte ou une base de test selon le contexte.

Pour partager les sessions avec l’autre API, conserver la même `SECRET_KEY`.

### Utiliser une base vide

Les migrations sont actuellement dans `../streamlit/alembic/`, à partir
de la racine du dépôt.

Suivre les instructions de migration du [README principal](../README.md)
en configurant la base souhaitée.

Le fichier `backend/api/init_db.py` contient encore des imports `src.db`
issus de l’ancienne organisation. Sa commande ne doit pas être utilisée
telle quelle pour cette version web.

## 3. Lancer le backend

Depuis `web/backend/`, avec l’environnement Python activé :

```bash
python -m uvicorn api.main:app --reload --port 8000 --env-file .env
```

Le point d’entrée est `api.main:app`.

L’option `--env-file .env` charge explicitement la configuration avant
l’import des modules, dont les chemins de recherche du `.env` diffèrent
encore dans le code actuel.

Le premier démarrage peut être plus long : le serveur charge les modèles
de recherche documentaire et prépare les bases de connaissances.

Attendre le message indiquant que le démarrage est terminé.

### Vérifier l’API

- Disponibilité : http://localhost:8000/health
- Documentation : http://localhost:8000/docs

La sonde de disponibilité doit renvoyer :

```json
{"status": "ok"}
```

Elle ne vérifie pas à elle seule le fonctionnement de PostgreSQL,
de Supabase Storage ou du fournisseur IA.

## 4. Installer le frontend

Dans un deuxième terminal, depuis la racine :

```bash
cd web/frontend
npm ci
```

Créer `web/frontend/.env.local` :

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Cette adresse est utilisée par le navigateur. Elle doit donc être accessible
depuis la machine sur laquelle l’interface est ouverte.

## 5. Lancer le frontend

Depuis `web/frontend/` :

```bash
npm run dev
```

Ouvrir http://localhost:3000, ou l’adresse affichée dans le terminal.

Redémarrer le serveur de développement après modification de `.env.local`.

## Fonctionnalités et API

| Fonction | Route principale |
|---|---|
| Inscription | `POST /auth/register` |
| Connexion | `POST /auth/login` |
| Profil | `GET /auth/me` |
| Sport préféré | `PATCH /auth/me` |
| Bibliothèque | `GET /matches` |
| Import vidéo | `POST /matches` |
| Détail d’un match | `GET /matches/{match_id}` |
| Analyse vidéo | `POST /matches/{match_id}/analyze` |
| Événements détectés | `GET /matches/{match_id}/events` |
| Suppression | `DELETE /matches/{match_id}` |
| Rapport de coaching | `POST /matches/{match_id}/coach-report` |
| Chat avec le coach | `POST /matches/{match_id}/chat` |
| Génération d’un plan | `POST /training-plan` |
| Historique des plans | `GET /training-plan` |

La documentation `/docs` précise les paramètres et les réponses attendues.
La présence d’une route ne signifie pas nécessairement qu’un écran dédié
existe dans le frontend.

Les routes protégées utilisent un token JWT envoyé dans l’en-tête
`Authorization: Bearer ...`.

## Modèles et connaissances

Le pipeline vidéo recherche par défaut :

```text
training/models/exported/padel_best.pt
training/models/exported/pickleball_best.pt
training/models/exported/tennis_best.pt
```

Ces chemins sont relatifs à la racine du dépôt.

Pour utiliser un autre emplacement, ajouter au `.env` du backend :

```dotenv
CV_WEIGHTS_DIR=/chemin/absolu/vers/les/modeles
```

Les connaissances et prompts des coachs sont dans `backend/agents/`.
Les index Chroma sont des données générées à partir des connaissances
sources et doivent rester hors du suivi Git.

## Tester le parcours complet

1. Créer un compte ou se connecter.
2. Choisir un sport.
3. Importer une courte vidéo où la balle et le terrain sont visibles.
4. Lancer l’analyse.
5. Attendre l’état `ready`, ou consulter l’erreur si l’état devient `failed`.
6. Ouvrir le match et vérifier les métriques.
7. Tester le chat.
8. Générer un plan d’entraînement après avoir obtenu des matchs analysés
   contenant des événements exploitables.

L’API lance l’analyse en tâche de fond. Le frontend consulte ensuite
l’état du match.

## Vérifications du frontend

Depuis `web/frontend/` :

```bash
npm run lint
npm run build
```

Pour lancer localement la version compilée :

```bash
npm run start
```

Le backend doit rester lancé séparément. La configuration
`NEXT_PUBLIC_API_URL` doit être définie lors de la compilation.

## Dépannage

| Symptôme | Vérification |
|---|---|
| Port 8000 déjà utilisé | Arrêter l’autre API ou choisir un autre port et adapter le frontend |
| `Failed to fetch` | Vérifier l’API, `NEXT_PUBLIC_API_URL` et la console du navigateur |
| `DATABASE_URL manquante` | Vérifier `backend/.env` et l’option `--env-file .env` |
| Table SQL inexistante | Vérifier la base ciblée et les migrations |
| Échec d’import vidéo | Vérifier le bucket `videos` et les accès Supabase |
| Modèle introuvable | Vérifier les fichiers `.pt` et `CV_WEIGHTS_DIR` |
| Erreur de coaching | Vérifier la clé Groq et les journaux du backend |
| Démarrage lent | Examiner le chargement des modèles et des connaissances RAG |

La configuration CORS actuelle est permissive pour le développement.
Avant un déploiement, la limiter aux origines réellement utilisées.

Les secrets du serveur doivent rester dans sa configuration et ne jamais
être inclus dans le code envoyé au navigateur.