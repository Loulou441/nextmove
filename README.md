# ⚽ NextMove - Coach Assistant & Job Engine

> Assistant virtuel intelligent pour les passionnés et les professionnels du sport. Analyse vidéo par ordinateur (Computer Vision), recommandations tactiques et recherche d'opportunités dans le milieu sportif.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## 🎯 Vue d'ensemble

NextMove est une plateforme hybride conçue pour transformer la performance sur le terrain et la carrière hors terrain. Elle combine la puissance de la **Computer Vision** pour l'analyse de jeu et des **LLMs** pour le coaching personnalisé.

### 💼 API SmartCoach (Port 8001)
API spécialisée pour l'analyse de vidéos et les recommandations de performance :
- 📄 **Analyse de vidéos automatique** : Détection des joueurs, du ballon et des événements via YOLOv8.
- 🔍 **Recommandations structurées** : Génération de feedbacks (Constat, Analyse, Action, Pro-Tip) basés sur les données extraites.

---

## ✨ Fonctionnalités principales

### 🏟️ Analyse de vidéos (SmartCoach)
- **Tracking Tactique** : Analyse des distances entre les lignes et du placement des joueurs.
- **Biomécanique** : Analyse de la posture (inclinaison du buste, pied d'appui) lors des tirs.
- **Extraction de KPIs** : Vitesse de pointe, taux de réussite des passes, et fréquence de "scans".
- **Feedback JSON** : Sortie structurée prête pour intégration mobile/web.

---

## 🚀 Installation rapide

### Prérequis
- Python 3.9+
- Clé API Groq & RapidAPI (pour le cerveau du Coach)

### Installation

```bash
# 1. Cloner le projet
git clone [https://github.com/votre-repo/tactique-ia.git](https://github.com/votre-repo/tactique-ia.git)
cd tactique-ia

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

## 📝 Licence

Ce projet est sous licence Apache 2.0. Voir le fichier [LICENSE](LICENSE) pour plus de détails.