# NextMove

NextMove analyse des vidéos de sports de raquette pour produire des
indicateurs de performance et des recommandations de coaching.

Le projet couvre le padel, le pickleball et le tennis. Il propose trois
interfaces : une application iOS, une application Streamlit et une
application web React / Next.js.

![Démonstration de détection sur une vidéo de padel](docs/media/demo_padel_nofield.gif)

## Les applications

| Application | Technologies | Analyse vidéo |
|---|---|---|
| iOS | SwiftUI, AVFoundation, Vision, Core ML | Sur l’appareil |
| Streamlit | Python, Streamlit, SQLAlchemy | Côté serveur avec YOLO |
| Web | React, Next.js, TypeScript, FastAPI | Côté serveur avec YOLO |

Les applications partagent un objectif produit et des modèles issus du
pipeline d’entraînement. Leurs implémentations et leur couverture
fonctionnelle restent distinctes.

## Organisation du dépôt

| Dossier | Contenu |
|---|---|
| `ios/` | Application Swift, projet Xcode et tests |
| `streamlit/` | Application Streamlit, services Python et migrations |
| `web/frontend/` | Interface React / Next.js |
| `backend/` | API FastAPI commune à React et iOS, services et agents |
| `training/` | Préparation des données, entraînement, évaluation et export |
| `docs/` | Documentation, exemples, maquettes et médias |
| `scripts/` | Vérifications et maintenance |

Fichiers de configuration à la racine :

- `.env.example` : exemple de configuration du serveur Python ;
- `.gitignore` : exclusions Git ;
- `packages.txt` : dépendances système utilisées pour le déploiement Python.

## Démarrage rapide

### Web React / Next.js

Lancer le backend Python et le frontend dans deux terminaux.

Les commandes, variables d’environnement et vérifications sont détaillées
dans [web/README.md](web/README.md).

### iOS

Depuis la racine :

```bash
open ios/nextmove.xcodeproj
```

Voir [ios/README.md](ios/README.md) pour les prérequis, la connexion à l’API
et la configuration du coaching.

### Streamlit

L’application est accessible en ligne :
**[Ouvrir NextMove Streamlit](https://nextmove-app.streamlit.app/)**.

Aucune installation locale n’est nécessaire pour l’utiliser. Son code reste
dans `streamlit/` ; elle appelle directement ses services Python.
Son déploiement n’héberge pas automatiquement l’API FastAPI.

## API et données

Une seule API HTTP est conservée, dans `backend/`, pour React et iOS.
Depuis la racine du dépôt, après installation et configuration :

```bash
python -m uvicorn backend.api.main:app --reload --port 8000
```

Voir [backend/README.md](backend/README.md) pour la configuration et le passage
depuis l’ancienne organisation. L’ancien dossier `streamlit/src/api/` a été retiré.

React utilise `NEXT_PUBLIC_API_URL`. iOS utilise `NEXTMOVE_API_URL`, avec
`http://localhost:8000` par défaut pour le simulateur. L’API se déploie séparément
de l’interface Streamlit.

Streamlit conserve ses services, son authentification et ses accès SQL.
Pour partager les comptes et accepter les tokens existants, configurer la même
base et la même `SECRET_KEY` côté Streamlit et backend.
Les vidéos et analyses iOS restent locales : ce déplacement n’ajoute pas de
synchronisation complète de sa bibliothèque et ne modifie pas son pipeline Core ML.

## Base de données et migrations

Les migrations sont conservées dans `streamlit/alembic/`.

Pour utiliser le `.env` racine avec la configuration Alembic actuelle,
exécuter depuis la racine, avec l’environnement Python activé :

```bash
python - <<'PY'
from pathlib import Path
import subprocess
import sys
from dotenv import load_dotenv

root = Path.cwd()
load_dotenv(root / ".env")

subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=root / "streamlit",
    check=True,
)
PY
```

Cette commande applique les migrations à la base définie dans
`DATABASE_URL`. Vérifier la base ciblée avant de l’exécuter.

Les fichiers `.env` et les clés privées ne doivent pas être versionnés.

## Modèles de vision

| Sport | iOS — Core ML | Python — YOLO |
|---|---|---|
| Padel | `ios/nextmove/Models/Padel/PadelDetector_v1.mlpackage` | `training/models/exported/padel_best.pt` |
| Pickleball | `ios/nextmove/Models/Pickleball/PickleballDetector_v1.mlpackage` | `training/models/exported/pickleball_best.pt` |
| Tennis | `ios/nextmove/Models/Tennis/TennisDetector_v1.mlpackage` | `training/models/exported/tennis_best.pt` |

Les deux pipelines Python recherchent par défaut les poids dans
`training/models/exported/`. La variable `CV_WEIGHTS_DIR` permet de choisir
un autre dossier ; utiliser de préférence un chemin absolu.

Les modèles Core ML sont des exports adaptés à l’application Apple.

Le code iOS mentionne également le badminton avec un repli sur le modèle
tennis. Aucun modèle badminton dédié n’est fourni.

## Entraînement

Le dossier `training/` contient :

- les configurations des sports dans `configs/` ;
- les scripts de préparation, d’entraînement et de validation ;
- les outils de conversion vers Core ML ;
- les notebooks Kaggle ;
- les poids exportés.

Les dépendances d’entraînement sont dans `training/requirements.txt`.
Utiliser un environnement Python séparé de celui des applications.

## Vérifications

Vérifier les fichiers et branchements du coaching iOS :

```bash
bash scripts/verify_llm_setup.sh
```

Ce script effectue des contrôles statiques. Il ne compile pas l’application
et ne valide pas les appels au fournisseur LLM.

Avant une fusion :

1. Compiler et tester iOS dans Xcode si la partie Apple est concernée.
2. Vérifier le démarrage de l’interface et de l’API concernées.
3. Tester la connexion, l’import vidéo et l’analyse.
4. Vérifier les résultats et les fonctionnalités de coaching.
5. Pour le frontend web, exécuter `npm run lint` et `npm run build`.

## Documentation

- [Application web](web/README.md)
- [Application iOS](ios/README.md)
- [API commune](backend/README.md)
- [Exemple de coaching iOS](docs/ios/USAGE_EXAMPLE_LLM.swift)
- [Maquettes](docs/mockups/)
- [Médias de démonstration](docs/media/)
