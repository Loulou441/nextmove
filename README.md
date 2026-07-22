<div align="center">

# 🏓 NextMove

Analyse de matchs multi-sport (Pickleball, Football, Padel) avec dashboards, détection de patterns et recommandations de coach IA (Groq).

</div>

---

## Overview

NextMove permet à un joueur d'importer ses matchs analysés, de consulter des dashboards de performance, de détecter des patterns de jeu récurrents et d'obtenir des recommandations de coaching générées par IA, sport par sport (Pickleball, Football, Padel).

---

## Pages de l'application

L'application est organisée en pages accessibles depuis la barre latérale ([app.py](app.py)) :

- **Me** — profil joueur, statistiques de progression, changement de sport.
- **Library** ([1_Library.py](src/streamlit_app/1_Library.py)) — liste des matchs analysés ou en attente d'analyse.
- **Upload** ([2_Upload.py](src/streamlit_app/2_Upload.py)) — import d'une nouvelle vidéo/d'un nouveau match.
- **Dashboard** ([3_Dashboard.py](src/streamlit_app/3_Dashboard.py)) — métriques clés et visualisations d'un match sélectionné.
- **AI Analysis** ([4_AI_Analysis.py](src/streamlit_app/4_AI_Analysis.py)) — génère un rapport de coaching IA pour une action précise, pour le sport choisi (Pickleball, Football ou Padel).
- **Patterns** ([5_Patterns.py](src/streamlit_app/5_Patterns.py)) — détection de tendances récurrentes dans le jeu.
- **Training Plan** ([6_Training_Plan.py](src/streamlit_app/6_Training_Plan.py)) — programme d'entraînement hebdomadaire personnalisé généré par l'agent IA (Pickleball).

---

## Repository Layout

```
nextmove/
├── app.py                     # point d'entrée Streamlit (navigation + page "Me")
├── requirements.txt           # dépendances Python (versions pinnées)
├── docs/
│   └── mockups/                # captures d'écran de référence (design)
├── data/
│   └── demo_games.csv         # jeu de données de démo
└── src/
    ├── config.py              # variables d'environnement, clés API, chemins des prompts
    ├── analysis_engine.py      # logique d'analyse des matchs
    ├── patterns_engine.py      # détection de patterns de jeu
    ├── design.py                # thème / composants UI iOS-like
    ├── viz.py                   # visualisations (terrain tactique, etc.)
    ├── streamlit_app/           # pages de l'application
    │   ├── 1_Library.py
    │   ├── 2_Upload.py
    │   ├── 3_Dashboard.py
    │   ├── 4_AI_Analysis.py
    │   ├── 5_Patterns.py
    │   └── 6_Training_Plan.py
    └── agents/                  # agents de coaching IA (un par sport)
        ├── agentmanager/         # classe de base partagée (client Groq)
        ├── agentpickelball/
        ├── agentfootball/
        └── agentpadel/
```

---

## Coaching IA multi-sport

Chaque sport dispose de son propre agent de coaching sous [src/agents/](src/agents) :

- `agentpickelball/` — contexte, prompt et données d'exemple pour le pickleball.
- `agentfootball/` — équivalent pour le football.
- `agentpadel/` — équivalent pour le padel.
- `agentmanager/` — classe de base partagée (client Groq).

Tous les agents renvoient le même schéma JSON (`constat`, `analyse`, `action_corrective`, `pro_tip`), affiché de façon identique dans l'UI Streamlit et en CLI (méthode `Agent.afficher_rapport()`, héritée par les 3 coachs).

## Prérequis

- Python 3.10+
- Une clé API [Groq](https://console.groq.com/) pour activer les recommandations IA (optionnelle : sans clé, l'app bascule en mode démo).

## Installation

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

Créer un fichier `.env` à la racine avec au minimum :

```
GROQ_API_KEY=votre_cle_groq
MODEL_NAME_PICKELBALL=llama-3.3-70b-versatile
MODEL_NAME_FOOTBALL=llama-3.3-70b-versatile
MODEL_NAME_PADEL=llama-3.3-70b-versatile
```

## Lancer l'application

```bash
streamlit run app.py
```

---

## Technical Details

- **Frontend/Backend** : Streamlit (Python), pas de séparation front/back — tout tourne dans le processus `streamlit run app.py`.
- **Données** : CSV de démo ([data/demo_games.csv](data/demo_games.csv)) et fichiers JSON d'exemple par sport.
- **IA** : API Groq (modèles type `llama-3.3-70b-versatile`) pour la génération des recommandations.
- **Visualisation** : Plotly pour les graphiques et le terrain tactique ([src/viz.py](src/viz.py)).

## Notes

- Sans `GROQ_API_KEY`, les pages "AI Analysis" et "Training Plan" affichent un rapport de démonstration statique.
- Les vidéos importées via la page Upload sont stockées localement dans `data/videos/` (non versionné, voir `.gitignore`).

---

## License

Ce projet est distribué sous licence MIT. Voir le fichier LICENSE pour plus d'informations.
