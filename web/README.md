# NextMove Web

Interface React / Next.js de NextMove. Elle appelle l’API commune à React et iOS,
désormais située dans `../backend/`. Le frontend reste dans `web/frontend/`.

## Backend

Suivre [les instructions du backend](../backend/README.md) pour installer les
dépendances, configurer PostgreSQL, Supabase, les clés IA et démarrer l’API.
Depuis la racine du dépôt, avec l’environnement Python activé :

```bash
python -m uvicorn backend.api.main:app --reload --port 8000
```

Disponibilité : http://localhost:8000/health ; documentation : http://localhost:8000/docs.
`/health` vérifie la réponse HTTP, pas les accès SQL, au stockage ou au fournisseur IA.

## Frontend

La version de Next.js verrouillée dans `frontend/package-lock.json` déclare
**Node.js >= 20.9.0**. C’est un minimum déclaré par la dépendance, pas une
version validée par un test complet du projet. Utiliser npm et conserver le
fichier de verrouillage avec `npm ci`.
Dans un second terminal, depuis la racine :

```bash
cd web/frontend
npm ci
```

Créer `web/frontend/.env.local` à partir de `.env.local.example` :

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Lancer :

```bash
npm run dev
```

Ouvrir http://localhost:3000 ou l’adresse indiquée dans le terminal.
L’adresse de l’API doit être accessible au navigateur. Redémarrer le frontend
après modification de `.env.local`. Aucune clé serveur ne doit figurer dans les
variables `NEXT_PUBLIC_*`.

## Organisation

| Dossier | Rôle |
|---|---|
| `frontend/app/` | Pages et layouts |
| `frontend/components/` | Composants visuels |
| `frontend/lib/api.ts` | Client HTTP |
| `frontend/lib/auth-context.tsx` | État d’authentification |
| `frontend/public/` | Ressources statiques |
| `../backend/` | API, services Python et agents |

## Tests manuels

1. S’inscrire ou se connecter et choisir un sport.
2. Importer une vidéo où la balle est visible.
3. Lancer l’analyse et suivre l’état jusqu’à `ready` ou `failed`.
4. Vérifier le détail, les événements et les métriques du match.
5. Tester le chat et les plans d’entraînement avec des matchs exploitables.

Les données utilisent la base configurée côté backend. Si elle est partagée
avec Streamlit, les créations et suppressions affectent les mêmes données.

## Compilation

Depuis `web/frontend/` :

```bash
npm run lint
npm run build
npm run start
```

La dernière commande sert la version compilée. Le backend reste un processus
distinct. `NEXT_PUBLIC_API_URL` doit être définie lors de la compilation.

## Dépannage

| Symptôme | Vérification |
|---|---|
| Failed to fetch | URL et disponibilité du backend, console navigateur |
| Port 8000 occupé | Arrêter l’ancienne API ou adapter le port et les clients |
| Erreur SQL | Configuration et migrations de la base ciblée |
| Échec d’import vidéo | Bucket privé `videos` et accès Supabase |
| Poids introuvables | `training/models/exported/` ou `CV_WEIGHTS_DIR` |
| Chat indisponible | Clé Groq, connaissances RAG et journaux du backend |

Les connaissances et modèles sont décrits dans [le README backend](../backend/README.md).
