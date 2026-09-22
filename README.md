# NextMove

NextMove analyse des vidéos de sports de raquette pour produire des
indicateurs de performance et des recommandations de coaching.

Le projet couvre le padel, le pickleball et le tennis, avec deux applications :

- **iOS** : interface SwiftUI et analyse vidéo sur l’appareil avec Core ML.
- **Streamlit** : interface Python et analyse vidéo côté serveur avec YOLO.

![Démonstration de détection sur une vidéo de padel](docs/media/demo_padel_nofield.gif)

## Organisation du dépôt

| Emplacement | Contenu |
|---|---|
| `ios/` | Application Swift, projet Xcode et tests |
| `streamlit/` | Application Streamlit, services Python, API et migrations |
| `training/` | Entraînement, évaluation et export des modèles |
| `docs/` | Documentation, exemples, maquettes et médias |
| `scripts/` | Vérifications et maintenance |
| `.env.example` | Exemple de configuration du serveur Python |
| `packages.txt` | Dépendances système pour le déploiement Python |

### Application iOS

| Emplacement | Rôle |
|---|---|
| `ios/nextmove.xcodeproj/` | Projet Xcode |
| `ios/nextmove/Models/` | Modèles de données et modèles Core ML |
| `ios/nextmove/Services/` | Analyse, tracking, coaching et client API |
| `ios/nextmove/ViewModels/` | État et logique de présentation |
| `ios/nextmove/Views/` | Écrans SwiftUI |
| `ios/nextmoveTests/` | Tests unitaires |
| `ios/nextmoveUITests/` | Tests d’interface |

### Application Streamlit

| Emplacement | Rôle |
|---|---|
| `streamlit/app.py` | Point d’entrée et navigation |
| `streamlit/requirements.txt` | Dépendances Python |
| `streamlit/alembic/` | Migrations de la base de données |
| `streamlit/alembic.ini` | Configuration Alembic |
| `streamlit/src/api/` | API FastAPI |
| `streamlit/src/auth/` | Authentification et sessions |
| `streamlit/src/db/` | Modèles SQLAlchemy et connexion SQL |
| `streamlit/src/services/` | Analyse vidéo, stockage et persistance |
| `streamlit/src/agents/` | Coaching IA, modération et recherche documentaire |
| `streamlit/src/streamlit_app/` | Pages de l’application |
| `streamlit/src/design.py` | Composants visuels |
| `streamlit/src/patterns_engine.py` | Calcul des patterns tactiques |

## Fonctionnement

### Analyse vidéo

Les vidéos sont traitées avec un modèle de détection propre au sport.
Les détections servent à calculer des métriques et à produire des retours
sur la performance.

Sur iOS, le pipeline utilise AVFoundation, Vision et Core ML.
Sur Streamlit, il utilise les modèles PyTorch avec Ultralytics YOLO.

Les deux applications possèdent leurs propres implémentations de l’analyse.
Leurs résultats et leurs fonctionnalités ne doivent donc pas être considérés
comme strictement identiques.

### Coaching

L’application iOS dispose d’un moteur de règles et d’un enrichissement LLM
optionnel.

Les agents Python utilisent Groq et une base de connaissances recherchée
avec ChromaDB et Sentence Transformers.

### Comptes et données

Streamlit utilise directement les services Python et la base PostgreSQL.
Les vidéos sont stockées dans Supabase Storage.

L’API FastAPI expose l’authentification et la liste des matchs du serveur.
Le client iOS utilise cette API pour la connexion et possède une méthode
de récupération des matchs.

La bibliothèque et les analyses iOS restent toutefois gérées localement :
la synchronisation complète entre les deux applications n’est pas réalisée.

## Démarrer Streamlit

### Prérequis

- Python compatible avec `streamlit/requirements.txt`.
- Une base PostgreSQL.
- Un projet Supabase Storage avec un bucket privé nommé `videos`.
- Une clé Groq pour les fonctionnalités appelant le LLM.

### Installation

Depuis la racine du dépôt :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r streamlit/requirements.txt
```

Sous PowerShell, activer l’environnement avec :

```powershell
.\.venv\Scripts\Activate.ps1
```

### Configuration

Créer un fichier `.env` à la racine à partir de `.env.example`, sans
écraser une configuration existante.

Renseigner notamment :

```dotenv
DATABASE_URL=postgresql://utilisateur:mot_de_passe@hote:5432/base
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_SERVICE_KEY=votre_cle_serveur
SECRET_KEY=votre_secret_jwt
GROQ_API_KEY=votre_cle_groq
```

Générer une valeur aléatoire pour `SECRET_KEY` :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Les fichiers `.env` et les clés privées ne doivent pas être versionnés.

### Migrations

L’application charge le `.env` racine, tandis que la configuration Alembic
actuelle cherche un `.env` dans `streamlit/`.

Pour utiliser la configuration racine sans la dupliquer, lancer cette
commande depuis la racine, avec l’environnement Python activé :

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

Les migrations s’appliquent à la base définie par `DATABASE_URL`.

### Interface

```bash
cd streamlit
python -m streamlit run app.py
```

Adresse par défaut : `http://localhost:8501`.

## Démarrer l’API

Dans un second terminal, activer l’environnement Python puis, depuis
`streamlit/` :

```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

- Disponibilité : `http://localhost:8000/health`
- Documentation interactive : `http://localhost:8000/docs`

Streamlit et FastAPI s’exécutent dans deux processus distincts.

### Routes disponibles

| Méthode | Route | Fonction |
|---|---|---|
| GET | `/health` | Disponibilité |
| POST | `/auth/register` | Inscription |
| POST | `/auth/login` | Connexion et token JWT |
| GET | `/auth/me` | Utilisateur connecté |
| GET | `/matches` | Matchs de l’utilisateur côté serveur |

Pour partager les comptes, l’API et Streamlit doivent utiliser la même
base et la même clé de signature JWT.

Voir [la documentation API](streamlit/src/api/README.md).

## Démarrer iOS

### Prérequis

- macOS avec une version de Xcode compatible avec le projet.
- Un appareil ou un simulateur compatible.
- Les modèles Core ML intégrés au projet.
- Une API accessible pour l’authentification.

Les réglages actuels du projet définissent une cible iOS **26.2**.
Vérifier cette valeur dans Xcode avant de choisir une destination.

### Ouvrir le projet

Depuis la racine :

```bash
open ios/nextmove.xcodeproj
```

Dans Xcode :

- sélectionner le schéma de l’application et la destination ;
- configurer la signature pour un appareil physique ;
- compiler avec `⌘B` ;
- lancer avec `⌘R` ;
- exécuter les tests avec `⌘U`.

### Adresse de l’API

Le client utilise par défaut `http://localhost:8000`.

Cette adresse convient au simulateur lorsque l’API tourne sur le Mac.
Sur un iPhone physique, configurer dans `NextMoveAPI` une adresse accessible
du Mac ou du serveur.

Pour exposer l’API sur le réseau local, depuis `streamlit/` :

```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Vérifier également les autorisations réseau et la configuration HTTP d’iOS.

### Configuration LLM locale

Le service iOS prend en charge :

| Variable | Utilisation |
|---|---|
| `OPENAI_API_KEY` | Clé du fournisseur |
| `OPENAI_API_BASE_URL` | URL personnalisée, optionnelle |
| `OPENAI_MODEL` | Modèle personnalisé, optionnel |
| `OPENAI_ORG_ID` | Organisation, optionnelle |

Pour un lancement de développement, les définir dans Xcode :

**Product → Scheme → Edit Scheme → Run → Arguments → Environment Variables**

Le fichier `.env` à la racine du dépôt n’est pas automatiquement lu
par l’application iOS. `ConfigurationManager` lit notamment l’environnement
du processus et peut chercher un fichier dans le bundle.

Ne pas intégrer de clé fournisseur dans une application distribuée.

Exemple :
[docs/ios/USAGE_EXAMPLE_LLM.swift](docs/ios/USAGE_EXAMPLE_LLM.swift).

## Modèles et entraînement

| Sport | Modèle iOS | Modèle Streamlit |
|---|---|---|
| Padel | `ios/nextmove/Models/Padel/PadelDetector_v1.mlpackage` | `training/models/exported/padel_best.pt` |
| Pickleball | `ios/nextmove/Models/Pickleball/PickleballDetector_v1.mlpackage` | `training/models/exported/pickleball_best.pt` |
| Tennis | `ios/nextmove/Models/Tennis/TennisDetector_v1.mlpackage` | `training/models/exported/tennis_best.pt` |

Les fichiers Core ML et PyTorch sont des formats distincts, adaptés
à chaque application.

Streamlit permet de personnaliser le dossier des poids avec
`CV_WEIGHTS_DIR`. Préférer un chemin absolu.

Les outils de préparation des données, d’entraînement, d’évaluation
et de conversion sont dans `training/scripts/`.
Leurs dépendances sont dans `training/requirements.txt`.

Le badminton apparaît également dans le code iOS avec un repli
sur le modèle tennis ; aucun modèle badminton dédié n’est fourni.

## Vérification de l’intégration LLM iOS

Depuis la racine :

```bash
bash scripts/verify_llm_setup.sh
```

Le script retrouve la racine depuis son propre emplacement.
Il peut donc être appelé depuis un autre répertoire avec son chemin complet.

Il vérifie :

- la présence des fichiers Swift et des tests attendus ;
- les références entre le pipeline et les services de coaching ;
- la prise en charge de la configuration LLM ;
- la présence de l’exemple de documentation.

Il ne compile pas l’application, ne contacte pas le fournisseur LLM
et ne valide pas la configuration d’un schéma Xcode.

## Vérifications après modification

1. Compiler et tester l’application iOS.
2. Vérifier l’inscription et la connexion.
3. Importer et analyser une vidéo dans chaque application.
4. Vérifier les résultats et le coaching.
5. Vérifier la disponibilité de l’API et les routes utilisées.

## Documentation

- [Maquettes](docs/mockups/)
- [Médias de démonstration](docs/media/)
- [Exemple de coaching iOS](docs/ios/USAGE_EXAMPLE_LLM.swift)
- [Documentation API](streamlit/src/api/README.md)