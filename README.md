# ⚽ NextMove (TactiCore) - SmartCoach IA

> **Assistant virtuel intelligent pour les passionnés et les professionnels du sport.**
> 
> Preuve de Concept combinant la **Vision par Ordinateur** (Computer Vision) et l'**IA Générative** (LLMs) pour l'analyse tactique automatisée.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green.svg)
![WebApp](https://img.shields.io/badge/Frontend-HTML5%2FJS-orange.svg)
![WebSocket](https://img.shields.io/badge/Sync-WebSocket-blueviolet.svg)
![Groq](https://img.shields.io/badge/AI-Groq_Llama_3-black.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

---

## 🎯 Mission

**NextMove** transforme l'analyse sportive en automatisant la détection d'actions et en générant des recommandations tactiques actionnables.

### Pipeline IA en 3 Étapes:

1. **🎥 Vision** : Tracking des joueurs et du ballon (YOLOv8 - prêt pour intégration)
2. **📊 Logique Métier** : Calcul géométrique des KPIs (vitesses, distances, passes)
3. **🧠 Cerveau IA** : Recommandations via LLM Groq spécialisé

*Note: Dans ce POC, les données d'extraction vidéo sont simulées pour démonstration. L'intégration YOLOv8 est planifiée.*

---

## ✨ Fonctionnalités Principales

L'application propose **5 modules clés** avec un design **Dark Mode Sportif** moderne:

| Module | Description |
|--------|-------------|
| 📊 **Dashboard** | Vue d'ensemble des stats, radar de performance (Technique, Tactique, Physique, Mental) |
| 🎬 **Analyse d'Actions** | Isoler une action, ajuster coordonnées X/Y, générer rapport coaching IA avec modélisation 2D |
| 🎥 **Timeline Séquentielle** | Naviguer dans tous les événements du match |
| 📈 **Patterns & Tendances** | Analyse comportementale (zones de danger, vulnérabilité en transition) |
| 📋 **Programme d'Entraînement** | To-Do list d'exercices personnalisés basée sur les erreurs |

---

## 🏗️ Architecture Moderne (Web-App)

Cette application utilise une **architecture Client-Serveur professionnelle**:

### Composants

```
┌─────────────────────────────────────────┐
│         FRONTEND (HTML/CSS/JS)          │
│  • Single Page App (SPA)                │
│  • Dark Mode Responsive                 │
│  • Dashboard, Matchs, Analysis, Metrics │
│  • WebSocket + Polling Sync             │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
    WebSocket     Polling (fallback)
    (temps réel)   (5s)
        │             │
┌──────────────────────┴──────────────────┐
│      BACKEND API (FastAPI - Python)    │
│  • RESTful + WebSocket                  │
│  • Validation Pydantic                  │
│  • Services métier isolés               │
│  • JWT-ready                            │
└──────────────┬───────────────────────┐
               │                       │
        ┌──────▼─────────┐      ┌─────▼────┐
        │  SQLite DB     │      │   Groq   │
        │  • Matches     │      │    AI    │
        │  • Actions     │      │          │
        │  • Metrics     │      └──────────┘
        └────────────────┘
```

### Stack Technique

| Couche | Technology |
|--------|------------|
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **Temps Réel** | WebSocket + Polling |
| **Database** | SQLite (evolvable → PostgreSQL) |
| **AI** | Groq API (Llama 3.3 70B) |
| **Data** | Pandas, JSON |

---

## 🚀 Démarrage Rapide (3 minutes)

### Prérequis

```bash
✅ Python 3.9+
✅ Port 8000 (Backend)
✅ Port 3000 (Frontend)
✅ Navigateur moderne
✅ (Optionnel) Clé API Groq
```

### Installation

```bash
# 1. Accéder au repo
cd nextmove

# 2. Rendre les scripts exécutables
chmod +x start-all.sh backend/run.sh frontend/run.sh

# 3. Démarrer tout (automatique)
./start-all.sh
```

### Accès

```
🌐 Frontend:    http://localhost:3000
📚 API Docs:    http://localhost:8000/docs
💓 Health:      http://localhost:8000/health
```

### Démarrage Manuel (2 terminaux)

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python -m http.server 3000
```

---

## 🎮 Test Immédiat

### 1. Créer un Match
1. Aller à **Matches** → **+ Nouveau Match**
2. Remplir: Équipe A, Équipe B, Sport, Date
3. Cliquer **Créer**

### 2. Tester la Synchronisation
1. Ouvrir 2 onglets: http://localhost:3000
2. Créer un match dans l'onglet 1
3. L'onglet 2 se met à jour **automatiquement** ✅

### 3. Explorer l'API
Visitez: http://localhost:8000/docs
```bash
# Test direct
curl http://localhost:8000/api/matches
```

---

## 📁 Structure du Projet

```
nextmove/
│
├── 🔵 BRANCHES
│   ├── main              # Production (Streamlit)
│   └── web-app ⭐       # Nouvelle version (FastAPI)
│
├── 📦 backend/           # Python FastAPI API
│   ├── main.py          # Entrée FastAPI
│   ├── config.py        # Configuration
│   ├── requirements.txt  # Dépendances
│   ├── app/
│   │   ├── models/      # Modèles Pydantic (Match, Action, Metrics)
│   │   ├── routes/      # Endpoints API (matches, sync)
│   │   ├── services/    # Logique métier (MatchService, SyncManager)
│   │   └── db/          # Base de données SQLite
│   └── run.sh           # Script démarrage
│
├── 🌐 frontend/          # Web UI moderne
│   ├── index.html        # SPA (Single Page App)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css # Styles Dark Mode (400+ lignes)
│   │   └── js/
│   │       ├── api-client.js   # Client REST API
│   │       ├── sync-client.js  # WebSocket + Polling
│   │       └── app.js          # Logique UI
│   └── run.sh            # Script démarrage
│
├── 🧠 src/               # Logique métier originale
│   ├── analysis_engine.py
│   ├── patterns_engine.py
│   ├── data_loader.py
│   └── ...
│
├── 📄 pages/             # Pages Streamlit originales
│   ├── Dashboard.py
│   ├── Match_Analysis.py
│   └── ...
│
├── 📊 data/              # Données de test
│   ├── demo_matches.csv
│   ├── demo_lineups.csv
│   └── demo_events.csv
│
└── 📚 Documentation
    ├── README.md              # 👈 Vous êtes ici
    ├── README-WEB-APP.md      # Architecture complète
    ├── ARCHITECTURE.md        # Détails techniques
    ├── MIGRATION_GUIDE.md     # Streamlit → WebApp
    └── QUICK-START.md         # Guide rapide
```

---

## 🔄 Synchronisation Temps Réel

### Concept: Multi-Devices

Imaginez 2 coaches qui consultent les données **en même temps**:

```
Coach 1 (Browser)          Backend         Coach 2 (Browser)
       │                      │                   │
       │─ Crée un match ─────>│                  │
       │                   [Save]                 │
       │                      │                   │
       │                  [Broadcast via WebSocket]
       │                      │─────────────────>│
       │<─ Confirm ──         │           [UI Update]
       │                      │
       │ (ou Polling all 5s si WebSocket échoue)
       │
       │─ Ajoute action ─────>│
       │                      │─────────────────>│
       │<─ OK                 │           [Auto-Sync]
```

### Modes Disponibles

| Mode | Vitesse | Fiabilité | Compatibilité |
|------|---------|-----------|---------------|
| **WebSocket** | ⚡ Immédiat | ✅ Excellente | ✅ Modern |
| **Polling** | ⏱️ 5 secondes | ✅ Bonne | ✅ Tous |

**Fallback automatique**: Si WebSocket échoue, bascule vers polling.

---

## 🔌 API Endpoints

### Matchs
```
POST   /api/matches              # Créer
GET    /api/matches              # Lister tous
GET    /api/matches/{id}         # Détails
PUT    /api/matches/{id}/status  # Changer statut
```

### Actions
```
POST   /api/matches/{id}/actions # Ajouter
GET    /api/matches/{id}/actions # Lister
```

### Métriques
```
POST   /api/matches/{id}/metrics # Sauvegarder
GET    /api/matches/{id}/metrics # Récupérer
```

### Synchronisation
```
WS     /api/sync/ws/{deviceId}           # WebSocket
GET    /api/sync/updates/{deviceId}      # Polling
POST   /api/sync/register/{deviceId}     # Register
```

---

## 📱 Support Multi-Plateforme

| Plateforme | Support |
|-----------|---------|
| 🖥️ **Desktop (Chrome, Firefox, Safari)** | ✅ Complet |
| 📱 **Mobile Web** | ✅ Responsive |
| 📲 **Native App** (via API) | ✅ Prêt |
| 🚀 **Offline** | ✅ Local Storage |

---

## 🔒 Sécurité

**Actuellement**: CORS ouvert pour développement

**À Implémenter**:
- [ ] JWT Authentication
- [ ] Role-Based Access Control (RBAC)
- [ ] Data Encryption
- [ ] Rate Limiting
- [ ] Input Validation (Pydantic)

---

## 🛠️ Configuration

### Fichier .env

```bash
# Backend
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# Frontend
FRONTEND_URL=http://localhost:3000

# AI
GROQ_API_KEY=your_key_here
```

---

## 📈 Roadmap

### ✅ Fait (web-app)
- Architecture FastAPI + WebApp
- Synchronisation WebSocket + Polling
- Dashboard temps réel
- CRUD Matchs/Actions/Metrics

### 🚧 À Faire
- [ ] Authentification JWT
- [ ] Recommandations IA via Groq
- [ ] Upload vidéo et extraction
- [ ] Graphiques avancés (Plotly)
- [ ] Mobile app native (React Native)
- [ ] PostgreSQL pour prod
- [ ] Docker + Deployment

### 🎯 Long Terme
- [ ] Vision par ordinateur (YOLOv8)
- [ ] Machine Learning prédictif
- [ ] Intégrations externes
- [ ] Déploiement Cloud (AWS)

---

## 📚 Documentation Détaillée

- **[README-WEB-APP.md](README-WEB-APP.md)** - Vue d'ensemble architecture
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Détails techniques profonds
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migration Streamlit → Web
- **[QUICK-START.md](QUICK-START.md)** - Démarrage ultra-rapide

---

## 🐛 Dépannage

### ❌ "Port 8000 already in use"
```bash
lsof -i :8000
kill -9 <PID>
```

### ❌ "WebSocket connection failed"
→ Normal! Frontend bascule automatiquement sur polling

### ❌ "CORS Error"
→ Vérifiez FRONTEND_URL dans .env

### ❌ "Module not found"
```bash
cd backend && pip install -r requirements.txt
```

---

## 🤝 Contribution

Pour contribuer à cette branche web-app:

```bash
git checkout -b feature/ma-feature
# Faire les changements
git commit -am 'feat: description'
git push origin feature/ma-feature
```

---

## 📞 Support & Questions

Voir les fichiers de documentation pour plus de détails ou consulter les logs:
```bash
# Logs frontend (Browser F12)
# Logs backend (Terminal)
```

---

## 📄 License

Apache 2.0 - Voir LICENSE

---

**Branche**: `web-app` (architectures moderne)  
**Branche**: `main` (Streamlit original)  
**Dernière mise à jour**: 18 mai 2026  
**Status**: 🟢 Prête pour développement
