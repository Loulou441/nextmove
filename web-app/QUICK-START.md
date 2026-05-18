# 🚀 TactiCore Web-App - Quick Start Guide

## ⚡ Démarrage en 3 minutes

### Étape 1: Préparation
```bash
# Aller au répertoire du projet
cd /Users/manont/Documents/Projets\ Hetic/Projet\ NextMove/nextmove

# Vérifier que vous êtes sur la branche web-app
git branch  # Devrait afficher: * web-app

# Rendre les scripts exécutables
chmod +x start-all.sh backend/run.sh frontend/run.sh
```

### Étape 2: Démarrer l'Application

#### Option A: Script Automatique (Recommandé)
```bash
./start-all.sh
```
Cela démarre:
- ✅ Backend (port 8000)
- ✅ Frontend (port 3000)
- ✅ Synchronisation WebSocket

#### Option B: Démarrage Manuel

**Terminal 1 - Backend:**
```bash
cd backend
bash run.sh
```
Attendez: "Application startup complete"

**Terminal 2 - Frontend:**
```bash
cd frontend
bash run.sh
```
Attendez: "Serving on http://0.0.0.0:3000"

### Étape 3: Accès

Ouvrez votre navigateur et allez à:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## 🎮 Test Rapide

### Créer un Match
1. Cliquer sur **"Matches"** dans la sidebar
2. Cliquer sur **"+ Nouveau Match"**
3. Remplir les détails:
   - Équipe A: "Paris FC"
   - Équipe B: "Lyon"
   - Sport: "football"
   - Date: Aujourd'hui
4. Cliquer **"Créer"**

### Vérifier la Synchronisation
1. Ouvrir une deuxième fenêtre de navigateur (http://localhost:3000)
2. Créer un match dans une fenêtre
3. L'autre fenêtre se met à jour **automatiquement** ✅

### Voir les Métriques API
Visitez http://localhost:8000/docs pour tester les endpoints:
- POST /api/matches (créer un match)
- GET /api/matches (lister)
- POST /api/matches/{id}/actions (ajouter une action)

## 📁 Structure de Fichiers Clé

```
backend/
├── main.py              # Point d'entrée
├── config.py            # Configuration
├── app/
│   ├── models/          # Modèles de données
│   ├── routes/          # Endpoints API
│   ├── services/        # Logique métier
│   └── db/              # Base de données
└── requirements.txt     # Dépendances Python

frontend/
├── index.html           # Application web
├── static/css/style.css # Styles (dark mode)
└── static/js/           # JavaScript
    ├── api-client.js    # Client API REST
    ├── sync-client.js   # WebSocket/Polling
    └── app.js           # Logique UI
```

## 🔧 Dépannage

### ❌ "Port 8000 already in use"
```bash
# Trouver le processus
lsof -i :8000

# Tuer le processus
kill -9 <PID>
```

### ❌ "WebSocket connection failed"
- Normal! Le frontend basculera automatiquement sur le polling
- Vérifiez que le backend est bien démarré
- Vérifiez les logs: `tail -f backend.log`

### ❌ "CORS Error"
- Vérifiez que FRONTEND_URL dans .env correspond à votre URL
- Par défaut: http://localhost:3000

## 📊 Voir les Données en Base

```bash
# Ouvrir SQLite
sqlite3 data/tacticore.db

# Lister les matchs
SELECT * FROM matches;

# Lister les actions
SELECT * FROM actions;

# Quitter
.exit
```

## 📚 Documentation Complète

- **[README-WEB-APP.md](README-WEB-APP.md)** - Vue d'ensemble
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Détails techniques
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Guide de migration

## 🌐 API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Créer un match
curl -X POST http://localhost:8000/api/matches \
  -H "Content-Type: application/json" \
  -d '{
    "team_a": "Paris",
    "team_b": "Lyon",
    "date": "2024-05-18T15:30:00",
    "sport": "football"
  }'

# Lister les matchs
curl http://localhost:8000/api/matches

# Voir la doc interactive
open http://localhost:8000/docs
```

## 🎯 Prochaines Étapes

### Court Terme
- [ ] Implémenter l'authentification JWT
- [ ] Ajouter les recommandations IA (Groq)
- [ ] Créer une app mobile (React Native)
- [ ] Ajouter les graphiques avancés

### Moyen Terme
- [ ] Migration PostgreSQL pour production
- [ ] Déploiement Docker
- [ ] CI/CD pipeline
- [ ] Tests automatisés

### Long Terme
- [ ] Vision par ordinateur (YOLOv8)
- [ ] Machine Learning
- [ ] Déploiement cloud (AWS/GCP)

## 💡 Tips & Tricks

### Déboguer le Frontend
```javascript
// Ouvrir la console (F12)
// Voir les requêtes API
console.log(apiClient)

// Vérifier l'état de sync
console.log(syncClient.isConnected)
```

### Déboguer le Backend
```bash
# Activer les logs détaillés
API_RELOAD=True python -m uvicorn main:app --log-level debug

# Voir toutes les requêtes
curl -v http://localhost:8000/api/matches
```

## 📞 Support

Pour des questions ou problèmes:
1. Vérifier les logs (F12 dans le navigateur ou terminal)
2. Consulter [ARCHITECTURE.md](ARCHITECTURE.md)
3. Vérifier que tous les ports sont libres

---

**Dernière mise à jour**: 18 mai 2026
**Branche**: web-app
**Status**: 🟢 Prêt pour développement
