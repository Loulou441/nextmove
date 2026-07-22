# 🏓 NextMove

Application Streamlit d'analyse sportive avec dashboards, détection de patterns et recommandations de coach IA (Groq).

## Overview

NextMove permet à un joueur d'importer ses matchs analysés, de consulter des dashboards de performance, de détecter des patterns de jeu récurrents et d'obtenir des recommandations de coaching générées par IA, sport par sport (Pickleball, Football, Padel).

## Repository Layout

```
nextmove/
├── app.py                     # point d'entrée Streamlit (navigation + page "Me")
├── requirements.txt           # dépendances Python
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

## Notes

- Chaque sport dispose de son propre agent de coaching (contexte, prompt, exemple de données) sous `src/agents/`, tous suivant le même schéma de réponse JSON (`constat`, `analyse`, `action_corrective`, `pro_tip`).
- Sans `GROQ_API_KEY`, les pages "AI Analysis" et "Training Plan" affichent un rapport de démonstration statique.
