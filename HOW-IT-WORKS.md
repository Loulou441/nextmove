# 🎓 Comment Fonctionne TactiCore Web-App

## 📚 Table des Matières

1. [Flux Global](#flux-global)
2. [Backend (FastAPI)](#backend-fastapi)
3. [Frontend (JavaScript)](#frontend-javascript)
4. [Synchronisation](#synchronisation)
5. [Exemples Concrets](#exemples-concrets)

---

## 🔄 Flux Global

Quand vous utilisez l'app, voici ce qui se passe:

```
┌─────────────┐
│   Utilisateur│─ Clique sur "Créer Match"
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  app.js (Frontend)                      │
│  function createMatch() {               │
│    apiClient.createMatch(data)          │
│  }                                      │
└──────┬──────────────────────────────────┘
       │ fetch() POST
       │ http://localhost:8000/api/matches
       │
       ▼
┌─────────────────────────────────────────┐
│  backend/main.py (FastAPI)              │
│  @router.post("/api/matches")           │
│  async def create_match(match: Match)   │
└──────┬──────────────────────────────────┘
       │
       ├─ Crée UUID
       ├─ Sauvegarde en BD (SQLite)
       └─ Crée SyncEvent
       │
       ▼
┌─────────────────────────────────────────┐
│  sync_service.py (SyncManager)          │
│  await broadcast_update(event)          │
│  • Ajoute à la queue de tous les devices│
│  • Envoie via WebSocket                 │
│  • Sauvegarde en BD                     │
└──────┬──────────────────────────────────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       ▼                                 ▼
┌──────────────┐              ┌──────────────┐
│ WebSocket    │              │ Polling      │
│ (immédiat)   │              │ (5 sec)      │
└──────┬───────┘              └──────┬───────┘
       │                             │
       ├─────────────┬───────────────┤
       │             │               │
       ▼             ▼               ▼
  Device A      Device B         Device C
 [UI Update]   [UI Update]     [UI Update]
```

---

## 🔧 Backend (FastAPI)

### 1. Structure des Fichiers

```
backend/
├── main.py              # Lance l'app FastAPI
├── config.py            # Configuration
└── app/
    ├── models/          # Définitions des structures
    ├── routes/          # Endpoints API
    ├── services/        # Logique métier
    └── db/              # Base de données
```

### 2. main.py - Le Point d'Entrée

```python
from fastapi import FastAPI

app = FastAPI(
    title="TactiCore API",
    version="1.0.0"
)

# CORS: permet au frontend d'appeler l'API
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Initialiser la BD
init_db()

# Inclure les routes
app.include_router(matches.router)
app.include_router(sync.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Ce qu'il fait**:
- ✅ Crée l'application FastAPI
- ✅ Configure CORS (autorise les requêtes du frontend)
- ✅ Crée la base de données
- ✅ Enregistre les routes (endpoints)

### 3. Modèles (models/__init__.py)

Les modèles **définissent la structure des données**:

```python
class Match(BaseModel):
    id: Optional[str] = None          # UUID généré
    team_a: str                        # "Paris FC"
    team_b: str                        # "Lyon"
    date: datetime                     # "2024-05-18T15:30:00"
    sport: str = "football"            # Type de sport
    status: str = "pending"            # État (pending, ongoing, completed)

class ActionAnalysis(BaseModel):
    match_id: str                      # Quel match?
    timestamp: float                   # À quel moment? (en secondes)
    action_type: str                   # "pass", "shoot", "tackle"
    coordinates: Dict[str, float]      # {"x": 50, "y": 60} (0-100)
    description: str                   # Texte libre
    ai_recommendation: Optional[str]   # Recommandation IA (optionnel)
```

**Avantage**: Pydantic **valide automatiquement** que les données sont correctes avant de les traiter.

### 4. Routes (routes/matches.py)

Les routes **reçoivent les requêtes et les traitent**:

```python
@router.post("/api/matches", response_model=dict)
async def create_match(match: Match):
    """
    Créer un nouveau match.
    
    Requête: POST /api/matches
    Body: {
        "team_a": "Paris",
        "team_b": "Lyon",
        "date": "2024-05-18T15:30:00",
        "sport": "football"
    }
    
    Réponse: {"id": "abc123", "message": "Match créé"}
    """
    try:
        # 1. Créer le match (sauvegarde en BD)
        match_id = MatchService.create_match(match)
        
        # 2. Notifier tous les devices
        await sync_manager.broadcast_update(SyncEvent(
            event_type="match_created",
            timestamp=datetime.now(),
            data={"match_id": match_id, "match": match.dict()}
        ))
        
        return {"id": match_id, "message": "Match créé avec succès"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Étapes**:
1. ✅ Reçoit les données du frontend
2. ✅ Valide avec Pydantic
3. ✅ Sauvegarde en BD
4. ✅ Crée un événement de sync
5. ✅ Diffuse à tous les clients
6. ✅ Retourne une réponse

### 5. Services (services/match_service.py)

Les services **contiennent la logique métier**:

```python
class MatchService:
    @staticmethod
    def create_match(match: Match) -> str:
        # Génère un ID unique
        match_id = str(uuid.uuid4())
        
        # Ouvre la connection à la BD
        with get_db() as conn:
            cursor = conn.cursor()
            
            # INSERT dans la table 'matches'
            cursor.execute("""
                INSERT INTO matches 
                (id, team_a, team_b, date, sport, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (match_id, match.team_a, match.team_b, 
                  match.date.isoformat(), match.sport, match.status))
            
            conn.commit()  # Valide la transaction
        
        return match_id
```

**Ce qu'il fait**:
- ✅ Crée un UUID unique pour le match
- ✅ Se connecte à la BD
- ✅ Exécute une requête SQL INSERT
- ✅ Valide (commit)
- ✅ Retourne l'ID

### 6. Base de Données (db/__init__.py)

La BD **stocke les données de manière persistante**:

```python
def init_db():
    """Crée les tables au démarrage"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crée la table 'matches'
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            team_a TEXT NOT NULL,
            team_b TEXT NOT NULL,
            date TEXT NOT NULL,
            sport TEXT DEFAULT 'football',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Crée d'autres tables...
    conn.commit()
    conn.close()
```

**Schéma SQLite**:

```
TABLE matches
├── id (clé primaire, unique)
├── team_a (texte)
├── team_b (texte)
├── date (texte ISO)
├── sport (texte)
├── status (texte)
└── created_at (timestamp)

TABLE actions
├── id (clé primaire)
├── match_id (référence à matches)
├── timestamp (nombre)
├── action_type (texte)
├── coordinates_x, coordinates_y (nombres)
├── description (texte)
└── ai_recommendation (texte)
```

### 7. Synchronisation (services/sync_service.py)

Le SyncManager **gère les connexions WebSocket et les files d'attente**:

```python
class SyncManager:
    def __init__(self):
        self.connected_clients = Set[str]    # {"device_1", "device_2"}
        self.sync_queue = Dict[str, list]    # {"device_1": [{event}, ...]}
    
    async def broadcast_update(self, event: SyncEvent):
        """Envoyer une mise à jour à TOUS les devices"""
        
        # 1. Sauvegarder l'événement en BD
        self._save_sync_event(event)
        
        # 2. Ajouter à la file d'attente de chaque client
        for device_id in self.connected_clients:
            if device_id not in self.sync_queue:
                self.sync_queue[device_id] = []
            self.sync_queue[device_id].append(event.dict())
    
    async def get_pending_updates(self, device_id: str):
        """Récupérer et vider la file d'attente"""
        updates = self.sync_queue.get(device_id, [])
        self.sync_queue[device_id] = []  # Vider
        return updates
```

---

## 🌐 Frontend (JavaScript)

### 1. Structure

```
frontend/
├── index.html                 # La page HTML
└── static/
    ├── css/style.css         # Les styles
    └── js/
        ├── api-client.js     # Appelle le backend
        ├── sync-client.js    # Reçoit les mises à jour
        └── app.js            # Logique de l'application
```

### 2. index.html - La Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>TactiCore</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <!-- Navigation -->
    <aside class="sidebar">
        <button class="nav-item" data-section="dashboard">Dashboard</button>
        <button class="nav-item" data-section="matches">Matchs</button>
        <button class="nav-item" data-section="analysis">Analyse</button>
    </aside>
    
    <!-- Contenu principal -->
    <main class="content">
        <!-- Section Dashboard -->
        <div id="dashboard" class="section active">
            <h2>Dashboard</h2>
            <div id="realtimeFeed" class="feed-list"></div>
        </div>
        
        <!-- Section Matchs -->
        <div id="matches" class="section">
            <h2>Gestion des Matchs</h2>
            <button id="createMatchBtn">+ Nouveau Match</button>
            <div id="matchesList"></div>
        </div>
    </main>
    
    <!-- Scripts -->
    <script src="/static/js/api-client.js"></script>
    <script src="/static/js/sync-client.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

### 3. api-client.js - Appeler le Backend

```javascript
class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL
    }
    
    async request(method, endpoint, data = null) {
        const url = `${this.baseURL}${endpoint}`
        
        const options = {
            method,
            headers: {'Content-Type': 'application/json'},
            body: data ? JSON.stringify(data) : null
        }
        
        try {
            // Envoyer la requête au backend
            const response = await fetch(url, options)
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            
            return await response.json()
        } catch (error) {
            console.error(`API Error:`, error)
            throw error
        }
    }
    
    // Méthodes spécialisées
    createMatch(matchData) {
        return this.request('POST', '/api/matches', matchData)
    }
    
    getMatches() {
        return this.request('GET', '/api/matches')
    }
    
    addAction(matchId, actionData) {
        return this.request('POST', `/api/matches/${matchId}/actions`, actionData)
    }
}

// Créer une instance globale
const apiClient = new APIClient('http://localhost:8000')
```

**Flux**:
1. Appelle `apiClient.createMatch(data)`
2. Utilise `fetch()` pour envoyer une requête HTTP
3. Convertit la réponse JSON
4. Retourne le résultat

### 4. sync-client.js - Recevoir les Mises à Jour

```javascript
class SyncClient {
    constructor(apiClient, baseURL = 'ws://localhost:8000') {
        this.apiClient = apiClient
        this.baseURL = baseURL
        this.deviceId = this.generateDeviceId()
        this.ws = null
        this.isConnected = false
        this.updateCallbacks = []
    }
    
    async connect() {
        // 1. Enregistrer le device au backend
        await this.apiClient.registerDevice(this.deviceId)
        
        // 2. Essayer WebSocket
        try {
            const wsURL = `${this.baseURL}/api/sync/ws/${this.deviceId}`
            this.ws = new WebSocket(wsURL)
            
            this.ws.onopen = () => {
                console.log('WebSocket connecté!')
                this.isConnected = true
            }
            
            this.ws.onmessage = (event) => {
                // Reçu un message du serveur
                const message = JSON.parse(event.data)
                this.handleMessage(message)
            }
            
            this.ws.onclose = () => {
                console.log('WebSocket fermé, passage au polling')
                this.isConnected = false
                this.startPolling()  // Fallback
            }
        } catch (error) {
            console.log('WebSocket échoué, utiliser polling')
            this.startPolling()
        }
    }
    
    startPolling() {
        // Demander les mises à jour toutes les 5 secondes
        setInterval(() => {
            this.apiClient.getUpdates(this.deviceId)
                .then(response => {
                    if (response.updates && response.updates.length > 0) {
                        response.updates.forEach(update => {
                            this.notifyCallbacks(update)
                        })
                    }
                })
        }, 5000)
    }
    
    onUpdate(callback) {
        // Enregistrer une fonction à appeler quand il y a une mise à jour
        this.updateCallbacks.push(callback)
    }
    
    notifyCallbacks(update) {
        // Appeler TOUTES les fonctions enregistrées
        this.updateCallbacks.forEach(callback => callback(update))
    }
}

const syncClient = new SyncClient(apiClient, 'ws://localhost:8000')
```

### 5. app.js - Logique de l'Application

```javascript
class TactiCoreApp {
    constructor() {
        this.currentMatch = null
        this.matches = []
        this.init()
    }
    
    async init() {
        // 1. Connecter à la sync
        await syncClient.connect()
        
        // 2. Écouter les mises à jour
        syncClient.onUpdate((update) => this.handleSyncUpdate(update))
        
        // 3. Initialiser les événements UI
        this.initEventListeners()
        
        // 4. Charger les données initiales
        await this.loadMatches()
    }
    
    initEventListeners() {
        // Quand on clique sur "Créer Match"
        document.getElementById('createMatchBtn').addEventListener('click', () => {
            this.openModal('createMatchModal')
        })
        
        // Quand on soumet le formulaire
        document.getElementById('createMatchForm').addEventListener('submit', (e) => {
            e.preventDefault()
            this.createMatch()
        })
        
        // Quand on clique sur un onglet
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                this.switchSection(e.target.closest('.nav-item'))
            })
        })
    }
    
    async createMatch() {
        const teamA = document.getElementById('teamA').value
        const teamB = document.getElementById('teamB').value
        const sport = document.getElementById('sport').value
        const date = new Date(document.getElementById('matchDate').value)
        
        try {
            // 1. Appeler le backend pour créer le match
            const response = await apiClient.createMatch({
                team_a: teamA,
                team_b: teamB,
                sport: sport,
                date: date.toISOString()
            })
            
            console.log('Match créé:', response)
            
            // 2. Fermer le modal
            document.getElementById('createMatchModal').classList.remove('active')
            
            // 3. Vider le formulaire
            document.getElementById('createMatchForm').reset()
            
            // 4. Recharger la liste
            await this.loadMatches()
        } catch (error) {
            console.error('Erreur:', error)
        }
    }
    
    async loadMatches() {
        try {
            // 1. Appeler le backend pour récupérer les matchs
            const response = await apiClient.getMatches()
            this.matches = response
            
            // 2. Mettre à jour l'UI
            this.renderMatches()
        } catch (error) {
            console.error('Erreur:', error)
        }
    }
    
    renderMatches() {
        const container = document.getElementById('matchesList')
        
        // Générer le HTML pour chaque match
        container.innerHTML = this.matches.map(match => `
            <div class="card">
                <h3>${match.team_a} vs ${match.team_b}</h3>
                <p>Sport: ${match.sport}</p>
                <p>Statut: ${match.status}</p>
            </div>
        `).join('')
    }
    
    handleSyncUpdate(update) {
        // Reçu une mise à jour du backend!
        console.log('Mise à jour reçue:', update.event_type)
        
        switch (update.event_type) {
            case 'match_created':
                // Recharger la liste
                this.loadMatches()
                this.showNotification('Nouveau match créé!')
                break
            
            case 'action_added':
                this.loadMatchActions(update.data.match_id)
                break
        }
    }
}

// Initialiser l'app au chargement
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TactiCoreApp()
})
```

---

## 🔄 Synchronisation

### Scénario: 2 Utilisateurs, 1 Backend

```
Coach 1                     Backend                 Coach 2
(Browser A)                 (FastAPI)              (Browser B)
    │                           │                      │
    │─ Crée un match ──────────>│                     │
    │  POST /api/matches        │                     │
    │                      [Save Match]               │
    │                      [Create Event]             │
    │                           │                     │
    │<─ Response ────           │                     │
    │                      [Broadcast]                │
    │                           │                     │
    │                    WebSocket Message             │
    │                           ├──────────────────>│
    │                           │                 [Event]
    │<─ WebSocket Message ──────┤                     │
    │    (Optional, aussi reçu  │            Browser syncs
    │     via polling)           │                [Reload]
    │                           │                     │
    │ [Reload]                  │                     │
    │ (ou auto via sync)        │                     │
    │                           │                     │
    ▼                           ▼                     ▼
 Match visible            Match saved           Match visible
 (Coach A)                (Database)             (Coach B)
```

### Modes de Sync

**WebSocket (Préféré)**
- Connexion persistante
- Mises à jour instantanées (< 100ms)
- Bidirectionnel

```javascript
const wsURL = 'ws://localhost:8000/api/sync/ws/device_123'
const ws = new WebSocket(wsURL)

ws.onmessage = (event) => {
    const update = JSON.parse(event.data)
    handleUpdate(update)  // Appliqué immédiatement
}
```

**Polling (Fallback)**
- Requêtes HTTP régulières (toutes les 5s)
- Plus universel (fonctionne partout)
- Latence: jusqu'à 5 secondes

```javascript
setInterval(async () => {
    const response = await fetch('/api/sync/updates/device_123')
    const data = await response.json()
    
    data.updates.forEach(update => handleUpdate(update))
}, 5000)
```

---

## 🎮 Exemples Concrets

### Exemple 1: Créer un Match

**Étape 1: L'utilisateur remplit le formulaire**
```
Équipe A: "Paris FC"
Équipe B: "Lyon"
Sport: "football"
Date: "2024-05-18 15:30"
```

**Étape 2: Clique sur "Créer"**
```javascript
// app.js - createMatch()
const response = await apiClient.createMatch({
    team_a: "Paris FC",
    team_b: "Lyon",
    sport: "football",
    date: "2024-05-18T15:30:00Z"
})
```

**Étape 3: Requête envoyée au backend**
```http
POST /api/matches HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "team_a": "Paris FC",
    "team_b": "Lyon",
    "sport": "football",
    "date": "2024-05-18T15:30:00Z"
}
```

**Étape 4: Backend traite (routes/matches.py)**
```python
@router.post("/api/matches")
async def create_match(match: Match):
    match_id = MatchService.create_match(match)
    
    await sync_manager.broadcast_update(SyncEvent(
        event_type="match_created",
        data={"match_id": match_id}
    ))
    
    return {"id": match_id}
```

**Étape 5: MatchService sauvegarde en BD**
```python
def create_match(match):
    match_id = str(uuid.uuid4())
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO matches
            (id, team_a, team_b, date, sport, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (match_id, match.team_a, match.team_b, ...))
        conn.commit()
    
    return match_id
```

**Étape 6: SyncManager notifie tous les devices**
```python
async def broadcast_update(event):
    # Ajouter à la queue de TOUS les devices
    for device_id in self.connected_clients:
        self.sync_queue[device_id].append(event)
```

**Étape 7: Frontend reçoit via WebSocket**
```javascript
ws.onmessage = (event) => {
    const update = JSON.parse(event.data)
    
    if (update.event_type === 'match_created') {
        app.handleSyncUpdate(update)  // Traiter
    }
}
```

**Étape 8: UI se met à jour**
```javascript
async handleSyncUpdate(update) {
    if (update.event_type === 'match_created') {
        await this.loadMatches()  // Recharger
        this.renderMatches()       // Afficher
    }
}
```

### Exemple 2: Polling Fallback

Si WebSocket est fermé:

```javascript
// sync-client.js - startPolling()
setInterval(() => {
    // Toutes les 5 secondes, demander les updates
    apiClient.getUpdates(this.deviceId)
        .then(response => {
            // {"updates": [{event_type: "match_created", ...}]}
            response.updates.forEach(update => {
                this.notifyCallbacks(update)
            })
        })
}, 5000)
```

Backend retourne les updates en attente:

```python
@router.get("/api/sync/updates/{device_id}")
async def get_updates(device_id: str):
    updates = await sync_manager.get_pending_updates(device_id)
    return {"updates": updates}
```

---

## 🔍 Débogage

### Voir ce qui se passe

**Frontend (Browser Console)**
```javascript
// Ouvrir F12 → Console

// Voir tous les matchs
apiClient.getMatches().then(m => console.log(m))

// Vérifier la connexion
console.log(syncClient.isConnected)  // true/false

// Voir les événements de sync
syncClient.onUpdate(e => console.log('Update:', e))
```

**Backend (Logs)**
```bash
# Terminal backend
# Les logs FastAPI s'affichent automatiquement

# Accéder à l'API directement
curl http://localhost:8000/api/matches

# Voir la doc interactive
open http://localhost:8000/docs
```

**Base de Données**
```bash
sqlite3 data/tacticore.db

# Lister tous les matchs
SELECT * FROM matches;

# Voir les actions
SELECT * FROM actions WHERE match_id = 'abc123';

# Quitter
.exit
```

---

## 📊 Flux Récapitulatif

```
USER INTERACTION
    ↓
frontend/app.js (JavaScript)
    ├─ Capture l'événement (click, submit, etc)
    ├─ Appelle apiClient
    ↓
frontend/api-client.js
    ├─ Construit la requête HTTP
    ├─ fetch() vers le backend
    ↓
HTTP REQUEST
    ↓
backend/main.py (FastAPI)
    ├─ Route trouvée (@router.post, etc)
    ↓
backend/routes/matches.py
    ├─ Valide avec Pydantic
    ├─ Appelle MatchService
    ↓
backend/services/match_service.py
    ├─ Logique métier
    ├─ Appelle get_db()
    ↓
backend/app/db/__init__.py
    ├─ Connexion SQLite
    ├─ SQL query (INSERT/SELECT/UPDATE)
    ├─ Commit/Fetch
    ↓
DATABASE (SQLite)
    ├─ Stocke/Récupère les données
    ↓
RESPONSE
    ↓
SyncManager
    ├─ Crée SyncEvent
    ├─ Ajoute à la queue de tous les devices
    ├─ Envoie via WebSocket OU
    ├─ Enregistre pour Polling
    ↓
HTTP RESPONSE au frontend
    ↓
backend/sync-client.js
    ├─ Reçoit via WebSocket OU
    ├─ Reçoit via Polling (5s)
    ↓
frontend/app.js
    ├─ handleSyncUpdate()
    ├─ app.loadMatches()
    ├─ app.renderMatches()
    ↓
DOM UPDATE
    ↓
USER SEES UPDATE
```

---

## 💡 Points Clés à Retenir

| Concept | Explication |
|---------|------------|
| **Modèles** | Définissent la structure des données (Match, Action, Metric) |
| **Routes** | Reçoivent les requêtes HTTP et les traitent |
| **Services** | Contiennent la logique métier (créer, lire, mettre à jour) |
| **Base de Données** | Stocke les données de manière persistante |
| **API Client** | Appelle le backend depuis le frontend via fetch() |
| **SyncManager** | Gère les connexions WebSocket et les files d'attente |
| **Polling** | Fallback si WebSocket échoue |
| **Events** | Notifie tous les clients des changements |

---

**Dernière mise à jour**: 18 mai 2026
