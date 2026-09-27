# NextMove iOS

Application native NextMove développée en SwiftUI.

Elle permet d’importer ou d’enregistrer une vidéo, de l’analyser sur
l’appareil avec Core ML et de consulter des indicateurs et des conseils
de coaching.

## Organisation

| Emplacement | Contenu |
|---|---|
| `nextmove.xcodeproj/` | Projet Xcode |
| `nextmove/Models/` | Modèles de données et modèles Core ML |
| `nextmove/Services/` | Traitement vidéo, détection, tracking, coaching et API |
| `nextmove/ViewModels/` | État et logique de présentation |
| `nextmove/Views/` | Écrans SwiftUI |
| `nextmove/Assets.xcassets/` | Ressources graphiques |
| `nextmoveTests/` | Tests unitaires |
| `nextmoveUITests/` | Tests d’interface |

Les chemins de ce tableau sont relatifs au dossier `ios/`.

## Prérequis

- macOS.
- Une version de Xcode compatible avec les réglages du projet.
- Un appareil ou un simulateur compatible.
- Les modèles Core ML présents dans le dépôt.
- Une API NextMove accessible pour l’authentification.

Le projet définit actuellement une cible iOS **26.2**.
Vérifier la cible dans les réglages Xcode avant de sélectionner une
destination d’exécution.

## Ouvrir le projet

Depuis la racine du dépôt :

```bash
open ios/nextmove.xcodeproj
```

Ou depuis `ios/` :

```bash
open nextmove.xcodeproj
```

Dans Xcode :

1. Sélectionner le schéma de l’application.
2. Choisir un simulateur ou un appareil compatible.
3. Pour un appareil physique, configurer l’équipe et la signature.
4. Compiler avec `⌘B`.
5. Lancer avec `⌘R`.

Conserver les sources et les dossiers de tests à côté du projet Xcode :
leurs références sont relatives à cette organisation.

## Connexion à l’API

Le client est défini dans :

```text
nextmove/Services/NextMoveAPI.swift
```

Il utilise par défaut :

```text
http://localhost:8000
```

### Simulateur

Configurer et démarrer le serveur commun en suivant
[backend/README.md](../backend/README.md). Depuis la racine du dépôt :

```bash
python -m uvicorn backend.api.main:app --reload --port 8000
```

La valeur par défaut `http://localhost:8000` convient au simulateur sur le Mac
qui exécute cette API. Vérifier `http://localhost:8000/health`.

### Adresse personnalisée et iPhone physique

Le client lit `NEXTMOVE_API_URL` dans l’environnement du processus (prioritaire),
puis dans Info.plist. Sans configuration, il utilise `http://localhost:8000`.
Une URL explicitement configurée doit être une adresse HTTP(S) absolue.

En développement, la définir dans Xcode :
**Product → Scheme → Edit Scheme → Run → Arguments → Environment Variables**.

Sur un iPhone physique, utiliser l’adresse réseau du Mac ou l’URL HTTPS du
serveur déployé ; `localhost` désigne le téléphone lui-même.
Pour rendre l’API locale accessible au réseau, depuis la racine :

```bash
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Production (Railway).** Le backend est déployé sur Railway. Pour pointer l’app
vers lui, renseigner la clé `NEXTMOVE_API_URL` dans
`ios/nextmove/Info.plist` avec l’URL HTTPS du service, par exemple :

```xml
<key>NEXTMOVE_API_URL</key>
<string>https://nextmove-production-9996.up.railway.app</string>
```

En HTTPS, aucune exception ATS n’est nécessaire. Vérifier
`https://<url>/health` avant une démonstration (le service peut se mettre en
veille sur l’offre gratuite ; le réveiller quelques minutes avant).

Vérifier le pare-feu, les autorisations réseau et la politique HTTP d’iOS.
L’application Streamlit en ligne n’est pas l’URL de cette API.

Les routes `/auth/register`, `/auth/login`, `/auth/me` et `/matches` sont
conservées. Réutiliser la même base et la même `SECRET_KEY` sur le serveur pour
conserver les comptes et accepter les tokens précédents.
Après migration, tester inscription, connexion, profil et lecture des matchs.

## Analyse vidéo

Le pipeline utilise notamment :

| Composant | Rôle |
|---|---|
| `VideoProcessor` | Extraction des images |
| `ModelManager` | Chargement des modèles Core ML |
| `ObjectDetector` | Détection avec Vision et Core ML |
| `ObjectTracker` | Suivi des objets |
| `FeatureExtractor` | Calcul des indicateurs |
| `AnalysisPipeline` | Orchestration et progression |
| `CoachingEngine` | Conseils fondés sur des règles |
| `EnhancedCoachingEngine` | Enrichissement LLM optionnel |

Les traitements vidéo sont exécutés sur l’appareil.
Les appels d’authentification et de coaching LLM nécessitent, eux,
une connexion au service correspondant.

## Modèles Core ML

| Sport | Emplacement relatif à `ios/` |
|---|---|
| Padel | `nextmove/Models/Padel/PadelDetector_v1.mlpackage` |
| Pickleball | `nextmove/Models/Pickleball/PickleballDetector_v1.mlpackage` |
| Tennis | `nextmove/Models/Tennis/TennisDetector_v1.mlpackage` |

Le badminton utilise un repli sur le modèle tennis ; aucun modèle dédié
au badminton n’est fourni.

Après un remplacement de modèle, vérifier sa présence dans le projet,
son inclusion dans la cible et son chargement à l’exécution.

Les outils d’entraînement et de conversion sont dans
[training/](../training/).

## Coaching IA (Groq)

NextMove utilise **Groq** comme unique fournisseur de LLM (aucun appel à
l’API OpenAI). Il y a deux chemins de coaching :

1. **Coaching serveur (recommandé) — LLM + RAG.** L’app appelle
   `POST /coach/recommendations` sur l’API commune. Le backend exécute le même
   agent coach par sport que le web et ancre la réponse sur des exercices réels
   (RAG / ChromaDB). C’est ce chemin qui donne les meilleurs conseils ; il ne
   requiert **aucune clé côté app**, seulement que l’API soit accessible.
2. **Enrichissement LLM local (optionnel).** `EnhancedCoachingEngine` peut
   appeler Groq directement depuis l’appareil. La configuration est lue par
   `ConfigurationManager.swift`.

### Clé Groq pour l’enrichissement local

La clé est fournie via un fichier **`Secrets.swift`** (non versionné). Copier
le gabarit et renseigner la clé :

```bash
cp ios/nextmove/Secrets.example.swift ios/nextmove/Secrets.swift
# puis dans Secrets.swift : renommer SecretsExample -> Secrets et coller groqAPIKey
```

Variables reconnues (toutes optionnelles — préfixe `GROQ_`) :

| Variable | Rôle |
|---|---|
| `GROQ_API_KEY` | Clé Groq |
| `GROQ_API_BASE_URL` | Endpoint (défaut `https://api.groq.com/openai/v1`) |
| `GROQ_MODEL` | Modèle (défaut `openai/gpt-oss-20b`, un modèle open hébergé par Groq) |

> Le nom `openai/gpt-oss-20b` est un modèle **open-weights hébergé par Groq** —
> ce n’est pas un appel à l’API OpenAI.

Pour un lancement local depuis Xcode, ces variables peuvent aussi être
définies dans **Product → Scheme → Edit Scheme → Run → Arguments →
Environment Variables**.

Sans clé (et sans API serveur joignable), le pipeline bascule sur un coaching
**fondé sur des règles**, de sorte que l’app produit toujours un résultat.

Ne pas distribuer d’application contenant une clé privée. `Secrets.swift` est
gitignored et réservé aux essais de développement.

Exemple :
[USAGE_EXAMPLE_LLM.swift](../docs/ios/USAGE_EXAMPLE_LLM.swift).

## Données et synchronisation

Les enregistrements et leurs analyses sont actuellement gérés localement
par l’application.

`NextMoveAPI` gère la connexion, l’inscription, la récupération du profil,
la lecture des matchs serveur, et la **synchronisation d’une analyse terminée**
vers la base partagée via `POST /matches/sync` (`syncMatch`).

Ainsi, une analyse faite sur iOS est **poussée vers la base commune** et
apparaît sur le web après connexion avec le même compte. Les vidéos, elles,
restent locales à l’appareil (seul le résultat d’analyse est envoyé) — ce
n’est donc pas une synchronisation complète de la médiathèque.

## Vérification de l’intégration

Depuis la racine du dépôt :

```bash
bash scripts/verify_llm_setup.sh
```

Depuis `ios/` :

```bash
bash ../scripts/verify_llm_setup.sh
```

Le script contrôle les fichiers et les références attendues.
Il ne compile pas Swift et ne valide pas les appels réseau.

## Tests

Dans Xcode, lancer les tests avec `⌘U`.

Les suites se trouvent dans :

- `nextmoveTests/` ;
- `nextmoveUITests/`.

Compléter les tests automatisés par un parcours manuel :

1. Inscription ou connexion.
2. Sélection du sport.
3. Import d’une vidéo.
4. Analyse et affichage des résultats.
5. Consultation du coaching et du chat.
6. Fermeture puis réouverture de l’application.

Vérifier les journaux : certains parcours prévoient un repli sur des données
de démonstration après un échec d’analyse. Un écran de résultats affiché
ne prouve donc pas à lui seul que l’analyse réelle a réussi.

## Dépannage

| Problème | Vérification |
|---|---|
| Connexion impossible | API démarrée, URL correcte et serveur accessible |
| Fonctionne en simulateur mais pas sur iPhone | Remplacer `localhost` et vérifier les autorisations réseau |
| Modèle introuvable | Présence du modèle, nom attendu et inclusion dans la cible |
| Erreur de signature | Équipe et réglages Signing & Capabilities |
| Destination incompatible | Version du système et cible de déploiement |
| Coaching IA indisponible | API `/coach/recommendations` joignable, clé Groq (`Secrets.swift`), journaux |
| Résultats de démonstration | Examiner l’erreur du pipeline réel et les options de repli |

## Documentation

- [Présentation du projet](../README.md)
- [Application web](../web/README.md)
- [Documentation de l’API commune](../backend/README.md)
- [Maquettes](../docs/mockups/)
- [Exemple de coaching](../docs/ios/USAGE_EXAMPLE_LLM.swift)
