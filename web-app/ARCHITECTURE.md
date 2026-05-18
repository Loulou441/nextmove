# 🏗️ Architecture Technique - TactiCore Web-App

## Vue d'ensemble

TactiCore Web-App est une application web moderne basée sur une architecture **API-First** avec synchronisation bidirectionnelle en temps réel.

## Composants Principaux

### 1. Backend API (FastAPI)

**Location**: `backend/`

#### Technologie
- **Framework**: FastAPI (async Python)
- **Serveur**: Uvicorn
- **Database**: SQLite (evolvable)
- **Validation**: Pydantic

#### Structure

```python
backend/
├── app/
│   ├── models/
│   │   └── __init__.py          # Modèles Pydantic
│   │
│   ├── routes/
│   │   ├── matches.py           # Endpoints matchs/actions/metrics
│   │   └── sync.py              # Endpoints synchronisation
│   │
│   ├── services/
│   │   ├── match_service.py     # Logique matchs
│   │   └── sync_service.py      # Logique sync
│   │
│   └── db/
│       └── __init__.py          # ORM/queries
│
├── main.py                       # Application FastAPI
└── config.py                    # Configuration
```

#### API Endpoints

**Matchs**
```
POST   /api/matches
GET    /api/matches
GET    /api/matches/{match_id}
PUT    /api/matches/{match_id}/status
```

**Actions**
```
POST   /api/matches/{match_id}/actions
GET    /api/matches/{match_id}/actions
```

**Métriques**
```
POST   /api/matches/{match_id}/metrics
GET    /api/matches/{match_id}/metrics
```

**Sync**
```
POST   /api/sync/register/{device_id}
POST   /api/sync/unregister/{device_id}
GET    /api/sync/updates/{device_id}
WS     /api/sync/ws/{device_id}
```

#### Modèles de Données

```python
# Match
{
    id: str
    team_a: str
    team_b: str
    date: datetime
    sport: str
    status: str  # pending, ongoing, completed
    metadata: dict
}

# Action
{
    id: str
    match_id: str
    timestamp: float
    action_type: str
    coordinates: {x, y}
    description: str
    ai_recommendation: str
    players_involved: [str]
}

# PerformanceMetrics
{
    match_id: str
    team: str
    technical_score: float
    tactical_score: float
    physical_score: float
    mental_score: float
    zones_activity: dict
}

# SyncEvent
{
    event_type: str  # match_created, action_added, metrics_updated
    timestamp: datetime
    data: dict
    device_id: str
}
```

### 2. Frontend Web

**Location**: `frontend/`

#### Technologie
- **Markup**: HTML5
- **Styling**: CSS3 (Dark Mode)
- **Interactivité**: JavaScript Vanilla (ES6+)
- **API Communication**: Fetch API
- **Temps Réel**: WebSocket + Polling

#### Structure

```javascript
frontend/
├── index.html                # Single Page Application
│
└── static/
    ├── css/
    │   └── style.css         # Tous les styles
    │
    └── js/
        ├── api-client.js     # Client REST API
        ├── sync-client.js    # Client WebSocket/Polling
        └── app.js            # Logique application
```

#### Architecture UI

```
┌─────────────────────────────────────────┐
│              HEADER                     │
│  Logo | Tagline |    Sync Status        │
├──────────────────┬──────────────────────┤
│                  │                      │
│   SIDEBAR NAV    │     CONTENT AREA     │
│                  │                      │
│  • Dashboard     │  [Dashboard Content] │
│  • Matches       │  [Matches Content]   │
│  • Analysis      │  [Analysis Content]  │
│  • Metrics       │  [Metrics Content]   │
│  • Settings      │  [Settings Content]  │
│                  │                      │
└──────────────────┴──────────────────────┘
```

#### Client API

```javascript
apiClient = new APIClient('http://localhost:8000')

// Matchs
apiClient.createMatch(matchData)
apiClient.getMatches()
apiClient.getMatch(matchId)
apiClient.updateMatchStatus(matchId, status)

// Actions
apiClient.addAction(matchId, actionData)
apiClient.getActions(matchId)

// Metrics
apiClient.saveMetrics(matchId, metricsData)
apiClient.getMetrics(matchId)

// Sync
apiClient.registerDevice(deviceId)
apiClient.getUpdates(deviceId)
```

#### Client Synchronisation

```javascript
syncClient = new SyncClient(apiClient, 'ws://localhost:8000')

// Connexion
await syncClient.connect()

// Écouter les mises à jour
syncClient.onUpdate((update) => {
    console.log('Mise à jour reçue:', update)
})

// Reconnexion automatique + fallback polling
```

### 3. Base de Données

**Type**: SQLite (local development)

#### Schéma

```sql
-- Matchs
CREATE TABLE matches (
    id TEXT PRIMARY KEY,
    team_a TEXT NOT NULL,
    team_b TEXT NOT NULL,
    date TEXT NOT NULL,
    sport TEXT DEFAULT 'football',
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Actions
CREATE TABLE actions (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    action_type TEXT NOT NULL,
    coordinates_x REAL,
    coordinates_y REAL,
    description TEXT,
    ai_recommendation TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(match_id) REFERENCES matches(id)
);

-- Métriques
CREATE TABLE performance_metrics (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    team TEXT NOT NULL,
    technical_score REAL,
    tactical_score REAL,
    physical_score REAL,
    mental_score REAL,
    zones_activity TEXT,  -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(match_id) REFERENCES matches(id)
);

-- Événements de sync
CREATE TABLE sync_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON
    device_id TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Synchronisation en Temps Réel

#### Flux WebSocket

```
Client                          Server
  │                              │
  │────────── CONNECT ──────────>│
  │                         [Accept]
  │                              │
  │  [Écoute passif]        [Registre device]
  │                              │
  │                    [Événement: action_added]
  │<─────── BROADCAST ───────────│
  │                              │
  │────── ACK + FETCH ──────────>│
  │<─── DATA PAYLOAD ────────────│
  │                              │
  │  [UI Update]            [Log event]
  │                              │
  │────── DISCONNECT ───────────>│
  │                         [Cleanup]
  │                              │
```

#### Fallback Polling (si WebSocket échoue)

```javascript
// Polling toutes les 5 secondes
setInterval(() => {
    apiClient.getUpdates(deviceId)
        .then(response => {
            response.updates.forEach(update => handleUpdate(update))
        })
}, 5000)
```

#### SyncManager

```python
class SyncManager:
    def __init__(self):
        self.connected_clients = Set[str]  # Devices connectés
        self.sync_queue = Dict[str, list]  # Queue d'événements par device
    
    async def connect(device_id):
        # Enregistrer le device
        self.connected_clients.add(device_id)
    
    async def broadcast_update(event):
        # Diffuser à tous les clients
        # Sauvegarder en BD
        # Ajouter à la queue de chaque client
    
    async def get_pending_updates(device_id):
        # Récupérer et vider la queue
```

## Flux de Données

### Création d'un Match

```
1. User clique "Créer Match" en UI

2. App.js appelle:
   apiClient.createMatch({team_a, team_b, date, sport})

3. Fetch POST vers backend:
   POST /api/matches
   Body: {team_a, team_b, date, sport, status: "pending"}

4. Backend (matches.py route):
   - Créer UUID
   - Insérer en DB
   - Créer SyncEvent
   - Broadcaster l'event

5. SyncManager.broadcast_update():
   - Sauvegarder l'event en DB
   - Ajouter à queue de tous les clients
   - Envoyer via WebSocket si connecté

6. SyncClient reçoit:
   - Appelle les callbacks onUpdate()
   - App.js gère l'event: handleSyncUpdate()
   - Recharge la liste des matchs
   - UI se met à jour

7. Tous les devices reçoivent la mise à jour
   - Via WebSocket (instantané)
   - Ou via Polling (5s max)
```

### Mise à Jour d'une Métrique

```
Phone App          Web App          Backend
    │                  │                │
    │                  │                │
    │  [User input metric]              │
    │                  │                │
    │                  ├── POST /api/matches/{id}/metrics
    │                  │                │
    │                  │          [Save to DB]
    │                  │                │
    │                  │          [Broadcast event]
    │                  │                │
    │ <───── WS UPDATE ────────────────│
    │                  │                │
    │   [Update UI]    │                │
    │  [Save locally]  │                │
    │                  │                │
    │                  │ <─ WS UPDATE ─│
    │                  │                │
    │                  │   [Update UI] │
    │                  │  [Save locally]│
    │                  │                │
```

## Authentification & Sécurité

### À Implémenter

```python
# JWT Tokens
from fastapi_jwt_extended import JWTManager, create_access_token

jwt_manager = JWTManager(app)

@router.post("/login")
async def login(credentials):
    # Valider user
    token = create_access_token(identity=user_id)
    return {"access_token": token}

@router.get("/api/matches")
@jwt_required()
async def get_matches():
    # Protégé
    pass
```

## Performance & Scalabilité

### Optimisations

1. **Pagination**: Limiter les résultats API
2. **Caching**: Redis pour les données fréquentes
3. **Compression**: gzip pour les réponses
4. **Indexing**: BD indexes sur match_id, device_id
5. **Connection Pooling**: Réutiliser les connexions DB

### Migration Production

```python
# SQLite → PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'sqlalchemy.dialects.postgresql',
        'NAME': 'tacticore_prod',
        'USER': 'postgres',
        'PASSWORD': os.env['DB_PASSWORD'],
        'HOST': 'localhost',
        'PORT': 5432,
    }
}
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### Docker Compose

```yaml
version: '3'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=tacticore
  
  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
```

## Debugging

### Logs

```bash
# Backend
tail -f backend/logs/api.log

# Frontend (Developer Console)
F12 → Console
```

### Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

---

**Dernière mise à jour**: 18 mai 2026
