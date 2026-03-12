README.md

# NextMove

Analyse vidéo de pickleball avec insights, dashboards et recommandations de type coach.

NextMove est une application iOS développée en SwiftUI qui analyse de courtes vidéos de pickleball pour transformer les séquences de jeu en insights compréhensibles, métriques simples et conseils d’amélioration.

![App Demo](frame 1.png)
---

# Overview

NextMove vise à rendre l’analyse de performance sportive plus accessible grâce à la vision par ordinateur et aux technologies mobiles.

À partir d’une courte vidéo de pickleball, l’application détecte les éléments clés du jeu, analyse les mouvements et génère automatiquement :

- des métriques simples de performance
- des visualisations et dashboards
- des recommandations de type coach en langage naturel

L’objectif est de permettre aux joueurs d’obtenir un retour rapide sur leurs séquences de jeu sans équipement spécialisé ni analyse complexe.

![App Demo](frame 3.png)
---

# How It Works

NextMove utilise un pipeline d’analyse vidéo en plusieurs étapes.

1. L’utilisateur importe une courte vidéo de pickleball
2. L’application extrait des images à partir de la vidéo
3. Un modèle de vision par ordinateur analyse chaque frame
4. Les objets détectés sont suivis dans le temps
5. Des métriques de jeu sont calculées
6. Les résultats sont transformés en insights et recommandations

![App Demo](frame 2.png)
### Pipeline d’analyse

Vidéo utilisateur ↓ Extraction des frames ↓ Détection d’objets via Core ML ↓ Tracking des objets ↓ Extraction de métriques ↓ Insights et recommandations ↓ Dashboard dans l’application


Le modèle est entraîné pour détecter différents éléments du jeu, tels que :

- la balle
- le joueur
- la raquette
- le filet
- les poteaux
- certaines structures du terrain

Ces détections permettent ensuite d’estimer des informations utiles sur le positionnement, les déplacements et la dynamique du rallye.

---

# Features
![App Demo](frame 4.png)
### Analyse vidéo

- import d’une vidéo depuis la galerie
- traitement des clips courts
- préparation de la vidéo pour l’analyse

### Détection visuelle

- détection du joueur et du contexte terrain
- détection de la balle lorsque possible
- identification de plusieurs éléments du jeu

### Génération d’insights

Les données extraites de la vidéo sont transformées en informations compréhensibles, par exemple :

- durée estimée du rallye
- position moyenne sur le terrain
- tendances de déplacement
- zones de couverture du joueur
![App Demo](frame 5.png)

### Recommandations coach

Les métriques sont reformulées en langage simple afin de fournir des conseils actionnables :

- améliorer le positionnement
- ajuster les déplacements
- anticiper certaines phases du jeu

### Dashboard de session
![App Demo](frame 6.png)

Chaque analyse génère un résumé visuel comprenant :

- métriques clés
- graphiques simples
- recommandations principales

---

# Technical Details

## Application iOS

NextMove est développé avec les technologies suivantes :

- Swift
- SwiftUI
- AVFoundation pour le traitement vidéo
- Vision pour la gestion des requêtes de vision par ordinateur
- Core ML pour l’inférence du modèle
- Swift Charts pour les visualisations
- SwiftData / Core Data pour le stockage des sessions

## Modèle de machine learning

Le modèle de détection est entraîné séparément en Python avant d’être converti au format Core ML pour l’application.

Pipeline d’entraînement :

- préparation et annotation des clips vidéo
- entraînement du modèle
- évaluation des performances
- conversion vers Core ML
- intégration dans l’application iOS

Technologies utilisées :

- Python
- PyTorch ou YOLO
- OpenCV
- outils d’annotation vidéo

Le modèle n’est pas entraîné dans l’application.  
Seule l’inférence est exécutée sur l’appareil mobile.

---

# Requirements

Pour exécuter le projet :

- macOS
- Xcode récent
- iOS 16 ou version ultérieure
- appareil iOS compatible ou simulateur
- modèle Core ML intégré au projet

---

# Installation

1. Cloner le dépôt :

git clone https://github.com/


2. Ouvrir le projet dans Xcode

3. Vérifier que le modèle `.mlmodel` est présent dans le dossier ML

4. Lancer l’application sur simulateur ou appareil

---

# License

Ce projet est distribué sous licence MIT.

Voir le fichier LICENSE pour plus d’informations.
