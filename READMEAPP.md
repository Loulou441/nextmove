<div align="center">

# NextMove — Guide de l'application

Analyse de matchs multi-sport (Pickleball, Football, Padel) avec insights, dashboards et recommandations de type coach IA.

NextMove est une application **Streamlit (Python)** qui transforme des données de match (importées ou de démo) en métriques simples, visualisations et conseils de coaching générés par un modèle de langage (Groq).

</div>

---

# Overview

NextMove vise à rendre l'analyse de performance sportive plus accessible. À partir des données d'un match, l'application génère automatiquement :

- des métriques simples de performance
- des visualisations et dashboards
- la détection de patterns de jeu récurrents
- des recommandations de type coach en langage naturel, propres à chaque sport

---

# Pages de l'application

L'application est organisée en pages accessibles depuis la barre latérale ([app.py](app.py)) :

- **Me** — profil joueur, statistiques de progression.
- **Library** ([1_Library.py](src/streamlit_app/1_Library.py)) — liste des matchs analysés ou en attente d'analyse.
- **Upload** ([2_Upload.py](src/streamlit_app/2_Upload.py)) — import d'une nouvelle vidéo/d'un nouveau match.
- **Dashboard** ([3_Dashboard.py](src/streamlit_app/3_Dashboard.py)) — métriques clés et visualisations d'un match sélectionné.
- **AI Analysis** ([4_AI_Analysis.py](src/streamlit_app/4_AI_Analysis.py)) — génère un rapport de coaching IA pour une action précise, pour le sport choisi (Pickleball ou Football).
- **Patterns** ([5_Patterns.py](src/streamlit_app/5_Patterns.py)) — détection de tendances récurrentes dans le jeu.
- **Training Plan** ([6_Training_Plan.py](src/streamlit_app/6_Training_Plan.py)) — programme d'entraînement hebdomadaire personnalisé généré par l'agent IA.

---

# Coaching IA multi-sport

Chaque sport dispose de son propre agent de coaching sous [src/agents/](src/agents) :

- `agentpickelball/` — contexte, prompt et données d'exemple pour le pickleball.
- `agentfootball/` — équivalent pour le football.
- `agentpadel/` — équivalent pour le padel.
- `agentmanager/` — classe de base partagée (client Groq).

Tous les agents renvoient le même schéma JSON (`constat`, `analyse`, `action_corrective`, `pro_tip`), affiché de façon identique dans l'UI Streamlit et en CLI (`afficher_rapport.py`).

Sans clé `GROQ_API_KEY` configurée, les pages "AI Analysis" et "Training Plan" basculent automatiquement en mode démo avec un rapport statique.

---

# Technical Details

- **Frontend/Backend** : Streamlit (Python), pas de séparation front/back — tout tourne dans le processus `streamlit run app.py`.
- **Données** : CSV de démo ([data/demo_games.csv](data/demo_games.csv)) et fichiers JSON d'exemple par sport.
- **IA** : API Groq (modèles type `llama-3.3-70b-versatile`) pour la génération des recommandations.
- **Visualisation** : Plotly pour les graphiques et le terrain tactique ([src/viz.py](src/viz.py)).

Voir [README.md](README.md) pour les instructions d'installation et de lancement.

---

# License

Ce projet est distribué sous licence MIT. Voir le fichier LICENSE pour plus d'informations.

