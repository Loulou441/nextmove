# 🚀 TactiCore - Architecture Web Moderne

## Vue d'ensemble

Cette branche `web-app` transforme TactiCore en une **application web moderne et scalable** avec:

- **Architecture Client-Serveur** : Séparation claire frontend/backend
- **Backend API** : FastAPI (haute performance, type-safe)
- **Frontend Web** : HTML5/CSS3/JavaScript moderne et responsive
- **Synchronisation Bidirectionnelle** : WebSocket + Polling pour temps réel
- **Base de Données** : SQLite (évolutive vers PostgreSQL)
- **Support Multi-Devices** : Les infos se synchronisent automatiquement

## 📁 Structure du Projet

```
nextmove/
├── backend/                    # Backend API (FastAPI)
│   ├── app/
│   │   ├── models/            # Modèles Pydantic
│   │   ├── routes/            # Endpoints API
│   │   ├── services/          # Logique métier
│   │   └── db/                # Gestion base de données
│   ├── main.py                # Point d'entrée
│   ├── config.py              # Configuration
│   ├── requirements.txt        # Dépendances Python
│   └── run.sh                 # Script de démarrage
│
├── frontend/                   # Frontend Web
│   ├── index.html             # Page principale
│   ├── static/
│   │   ├── css/style.css      # Styles (Dark Mode)
│   │   └── js/
│   │       ├── api-client.js          # Client API
│   │       ├── sync-client.js         # Client sync temps réel
│   │       └── app.js                 # Logique UI
│   └── run.sh                 # Script de démarrage
│
├── src/                        # Code original (logique métier)
├── pages/                      # Pages Streamlit originales
├── data/                       # Fichiers de données
│
├── start-all.sh               # Script démarrage complet
├── README-WEB-APP.md          # Cette documentation
└── ARCHITECTURE.md            # Détails architecture
```

## 🔄 Architecture et Synchronisation

### Flux de Données

```
┌─────────────────────────────────────────────────┐
│                                                 │
│            Frontend Web (Browser)               │
│  ┌───────────────────────────────────────────┐  │
│  │ • Dashboard                               │  │
│  │ • Gestion Matchs                          │  │
│  │ • Analyse Actions                         │  │
│  │ • Métriques Performance                   │  │
│  └───────────────────────────────────────────┘  │
│                     │                           │
│          ┌──────────┴──────────┐               │
│          │                     │               │
│      WebSocket             Polling             │
│      (Temps réel)      (Fallback)             │
│          │                     │               │
└──────────┼─────────────────────┼──────────────┘
           │                     │
┌──────────┼─────────────────────┼──────────────┐
│          │                     │              │
│      ┌───▼─────────────────────▼────┐        │
│      │    Backend API (FastAPI)     │        │
│      ├────────────────────────────┤        │
│      │ • /api/matches             │        │
│      │ • /api/matches/:id/actions │        │
│      │ • /api/matches/:id/metrics │        │
│      │ • /api/sync/ws/:deviceId   │        │
│      │ • /api/sync/updates/:id    │        │
│      └──────────┬─────────────────┘        │
│                 │                          │
│           ┌─────▼──────┐                  │
│           │ Database   │                  │
│           │ (SQLite)   │                  │
│           └────────────┘                  │
│                                           │
└───────────────────────────────────────────┘

       Sync Manager
       ├── Enregistre les devices
       ├── Diffuse les mises à jour
       └── Gère les queues d'événements
```

### Modes de Synchronisation

#### 1. **WebSocket (Prioritaire - Temps Réel)**
- Connexion persistante avec le serveur
- Mises à jour instantanées
- Bidirectionnel
- Reconnexion automatique

#### 2. **Polling (Fallback)**
- Requêtes HTTP régulières (5s)
- Si WebSocket échoue
- Synchronisation régulière garantie
- Compatible avec tous les navigateurs

## 🚀 Démarrage

### Prérequis
- Python 3.9+
- Navigateur moderne (Chrome, Firefox, Safari, Edge)
- Port 8000 libre (Backend)
- Port 3000 libre (Frontend)

### Installation Rapide

```bash
# 1. Cloner/accéder au répertoire
cd nextmove

# 2. Rendre les scripts exécutables
chmod +x *.sh
chmod +x backend/run.sh
chmod +x frontend/run.sh

# 3. Démarrer tout
./start-all.sh
```

### Démarrage Manuel

**Terminal 1 - Backend:**
```bash
cd backend
bash run.sh
# Ou directement:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
bash run.sh
# Ou directement:
python -m http.server 3000
```

Accès:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentation API**: http://localhost:8000/docs

## 📊 Fonctionnalités

### Dashboard
- Vue d'ensemble des statistiques
- Flux d'événements en temps réel
- Métrique de synchronisation

### Gestion des Matchs
- Créer/modifier/supprimer des matchs
- Gérer le statut (pending, ongoing, completed)
- Vue temporelle

### Analyse d'Actions
- Ajouter une action à un match
- Coordonnées sur le terrain
- Intégration IA pour recommandations

### Métriques de Performance
- Scores techniques/tactiques/physiques/mentaux
- Zones d'activité
- Historique des performances

### Synchronisation
- Voir l'état de la connexion
- Basculer entre WebSocket et Polling
- Historique des events

## 🔌 API Endpoints

### Matchs
```
POST   /api/matches              # Créer un match
GET    /api/matches              # Lister tous les matchs
GET    /api/matches/{id}         # Récupérer un match
PUT    /api/matches/{id}/status  # Mettre à jour le statut
```

### Actions
```
POST   /api/matches/{id}/actions # Ajouter une action
GET    /api/matches/{id}/actions # Lister les actions
```

### Métriques
```
POST   /api/matches/{id}/metrics # Sauvegarder les métriques
GET    /api/matches/{id}/metrics # Récupérer les métriques
```

### Synchronisation
```
POST   /api/sync/register/{deviceId}    # Enregistrer un device
POST   /api/sync/unregister/{deviceId}  # Désenregistrer
GET    /api/sync/updates/{deviceId}     # Polling
WS     /api/sync/ws/{deviceId}          # WebSocket
```

## 📱 Intégration Mobile

Le frontend est entièrement responsive et fonctionne sur mobile. Pour créer une application native (React Native, Flutter), utilisez les endpoints API:

```javascript
// Exemple: Créer un match depuis une app mobile
fetch('http://localhost:8000/api/matches', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        team_a: "Paris FC",
        team_b: "Lyon",
        date: new Date().toISOString(),
        sport: "football"
    })
})
```

## 🔐 Sécurité (À Implémenter)

- [ ] Authentification (JWT)
- [ ] Autorisation par rôle (admin, coach, player)
- [ ] Chiffrement des données sensibles
- [ ] Rate limiting
- [ ] CORS réstraint
- [ ] Validation des inputs

## 📈 Évolutions Futures

### Court Terme
- [ ] Intégration Groq API pour recommandations IA
- [ ] Upload vidéo et extraction actions
- [ ] Graphiques et visualisations avancées
- [ ] Export PDF des rapports

### Moyen Terme
- [ ] Authentification et profils utilisateur
- [ ] Collaboration temps réel (plusieurs coaches)
- [ ] Mobile app native (React Native)
- [ ] Migration PostgreSQL pour production

### Long Terme
- [ ] Vision par ordinateur (YOLOv8)
- [ ] Machine Learning pour prédictions
- [ ] Intégrations tiers (stats externes)
- [ ] Deployment cloud (AWS, GCP, Azure)

## 🛠️ Configuration

### Variables d'environnement (.env)

```bash
# Backend
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# API Keys
GROQ_API_KEY=your_key_here

# Database
DB_PATH=./data/tacticore.db

# Frontend
FRONTEND_URL=http://localhost:3000
```

## 📚 Documentation Techniques

Voir [ARCHITECTURE.md](./ARCHITECTURE.md) pour les détails d'implémentation.

## 🤝 Contribution

Pour contribuer à cette branche web-app:

1. Créer une branche feature: `git checkout -b feature/nom`
2. Faire les changements
3. Commit: `git commit -am 'Description'`
4. Push: `git push origin feature/nom`
5. Créer une Pull Request

## 📝 License

Apache 2.0 - Voir LICENSE

---

**Dernière mise à jour**: 18 mai 2026
**Branche**: web-app
**Version**: 1.0.0
