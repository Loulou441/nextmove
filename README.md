# ⚽ NextMove (TactiCore) - SmartCoach IA

> **Assistant virtuel intelligent pour les passionnés et les professionnels du sport.** > *Preuve de Concept (POC) : Combinaison de la Vision par Ordinateur (Computer Vision) et de l'IA Générative (LLMs) pour l'analyse tactique automatisée.*

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)
![Groq](https://img.shields.io/badge/AI-Groq_Llama_3-black.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

---

## Lien vers le prototye fonctionnel.
https://nextmovetacticore.streamlit.app/
*Attention, la partie coach du prototype ne fonctionnera pas car une clé API Groq est nécessaire.*

---

## 🎯 La Mission
NextMove a pour objectif d'automatiser l'analyse sportive, quel que soit le niveau (amateur ou pro) ou le sport (Football, Pickleball). 
Ce projet démontre qu'il est possible de transformer un flux vidéo brut en **recommandations tactiques et techniques actionnables**, grâce à un pipeline en 3 étapes :
1. **Vision** : Tracking des joueurs et du ballon (YOLOv8).
2. **Logique Métier** : Calcul géométrique des KPIs (vitesses, distances, lignes de passes).
3. **Cerveau IA** : Interprétation cognitive et coaching par un LLM spécialisé.

*(Note : Dans ce POC interactif, la partie Computer Vision est simulée via des jeux de données pré-extraits afin de démontrer en temps réel la puissance du moteur d'analyse IA).*

---

## ✨ Fonctionnalités du Dashboard (POC)

L'application est divisée en 5 modules clés, habillés d'un design personnalisé "Dark Mode Sportif" :

* 📊 **Dashboard Global** : Vue d'ensemble des statistiques du match, radar de performance (Technique, Tactique, Physique, Mental) et répartition des zones de jeu.
* 🎬 **Analyse d'Action Vidéo** : Interface permettant d'isoler une action (ex: perte de balle, tir), d'ajuster les coordonnées X/Y, et de générer un rapport de coaching IA instantané avec modélisation 2D du terrain.
* 🎥 **Analyse Séquentielle (Timeline)** : Navigation dans la timeline complète des événements du match extraits par la Vision.
* 📈 **Tendances & Patterns** : Analyse macroscopique des comportements de l'équipe (Zones de danger, vulnérabilité en transition).
* 📋 **Programme d'Entraînement** : Synthèse globale générant une "To-Do List" d'exercices personnalisés basés sur les erreurs du match.

---

## 🛠️ Stack Technique

* **Interface Web :** [Streamlit](https://streamlit.io/)
* **Visualisation de Données :** Plotly Express & Plotly Graph Objects
* **Intelligence Artificielle :** API Groq (Modèle `llama-3.3-70b-versatile`)
* **Manipulation de Données :** Pandas, JSON
* **Styling :** CSS injecté & Configuration `.toml`

---

## 🚀 Installation & Lancement en local

### 1. Prérequis
* Python 3.9 ou supérieur.
* Une clé API gratuite [Groq](https://console.groq.com/).

### 2. Cloner le dépôt
```bash
git clone [https://github.com/Loulou441/nextmove.git](https://github.com/Loulou441/nextmove.git)
cd nextmove
