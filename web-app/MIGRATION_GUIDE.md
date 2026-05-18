# Migration Guide: Streamlit → Web App Architecture

## 📋 Guide de Migration

Ce document explique comment l'architecture Streamlit a été transformée en une application web moderne.

## Avant & Après

### AVANT (Streamlit)
```
app.py
├── Streamlit page configurable
├── Affichage immédiat
├── Logique et UI mélangées
└── État dans la session Streamlit

pages/
├── Dashboard.py
├── Match_Analysis.py
├── Recommendations.py
└── Autres pages...
```

**Limitations**:
- ❌ Difficile à synchroniser entre plusieurs clients
- ❌ État partagé complexe
- ❌ Performance UI dégradée
- ❌ Peu extensible
- ❌ Mobile limité

### APRÈS (Web App)
```
backend/app/
├── API RESTful avec WebSocket
├── Logique métier isolée
├── Base de données persistante
└── Multi-clients supporté

frontend/
├── UI moderne et responsive
├── WebSocket pour temps réel
├── Local storage pour offline
└── Mobile-friendly
```

**Avantages**:
- ✅ Synchronisation bidirectionnelle
- ✅ Performance excellente
- ✅ Très extensible
- ✅ Support complet mobile
- ✅ Déployable partout

## 🔄 Migration des Composants

### 1. Logique Métier (src/)

**Avant**:
```python
# src/analysis_engine.py
def analyze_action(action_data):
    # ...analyse...
    return recommendations
```

**Après**:
```python
# backend/app/services/analysis_service.py
class AnalysisService:
    @staticmethod
    def analyze_action(action_data):
        # ...analyse...
        return recommendations
```

**Migration**:
- ✅ Copier la logique dans les services backend
- ✅ Ajouter des endpoints API
- ✅ Appeler depuis le frontend

### 2. Pages Streamlit (pages/)

**Avant**:
```python
# pages/Dashboard.py
import streamlit as st
st.set_page_config(...)
st.title("Dashboard")
# UI + logique mélangées
```

**Après**:
```javascript
// frontend/static/js/app.js
// Section dans le HTML
<div id="dashboard" class="section active">
    <h2>Dashboard</h2>
    <!-- Contenu -->
</div>

// Logique JavaScript
function loadDashboard() {
    apiClient.getMetrics().then(data => {
        // Afficher les données
    })
}
```

**Migration par page**:
| Page Streamlit | Nouveau Module |
|---|---|
| Dashboard.py | `#dashboard` section + `loadDashboard()` |
| Match_Analysis.py | `#analysis` section + `loadMatchActions()` |
| Recommendations.py | Intégré dans les métriques |
| Video_Action_Analysis.py | Module `analysis` |
| Match_Patterns.py | Module `metrics` |

### 3. Visualisations

**Avant**:
```python
import plotly.express as px
fig = px.scatter(...)
st.plotly_chart(fig)
```

**Après**:
```javascript
// Canvas HTML5
const canvas = document.getElementById('pitchCanvas')
const ctx = canvas.getContext('2d')
// Dessiner le terrain et les positions
```

**Ou** utiliser Plotly.js côté client:
```html
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<div id="plot"></div>
<script>
Plotly.newPlot('plot', data, layout)
</script>
```

### 4. État de l'Application

**Avant**:
```python
# État Streamlit (rechargé à chaque interaction)
if 'matches' not in st.session_state:
    st.session_state.matches = load_matches()
```

**Après**:
```javascript
// État JavaScript (persistent)
class TactiCoreApp {
    constructor() {
        this.matches = []
        this.currentMatch = null
    }
    
    async loadMatches() {
        this.matches = await apiClient.getMatches()
        this.render()
    }
}
```

## 📦 Modèles de Données

### Match

**Avant**:
```python
{
    "team_a": "Paris",
    "team_b": "Lyon",
    "date": "2024-05-18"
}
```

**Après**:
```python
class Match(BaseModel):
    id: str
    team_a: str
    team_b: str
    date: datetime
    sport: str
    status: str
```

### Action

**Avant** (simulée):
```json
{
    "timestamp": 123.4,
    "player": "10",
    "action": "pass"
}
```

**Après**:
```python
class ActionAnalysis(BaseModel):
    id: str
    match_id: str
    timestamp: float
    action_type: str
    coordinates: {"x": 50, "y": 60}
    description: str
    ai_recommendation: str
```

## 🔌 Endpoints à Créer

Migrer chaque fonctionnalité Streamlit vers un endpoint:

```python
# Avant: st.write(analyze_action(action_data))
# Après:
@router.post("/api/matches/{match_id}/actions")
async def add_action(match_id: str, action: ActionAnalysis):
    # Logique du dashboard
    return {"id": action_id, "message": "Action enregistrée"}
```

## 🎨 UI/UX

### Streamlit
- Widgets simples
- Responsive auto
- Thème limité

### Web App
- CSS personnalisé
- Dark Mode sportif
- Animations fluides
- Mobile-first
- Accessibilité

## 🚀 Avantages de la Migration

| Aspect | Streamlit | Web App |
|---|---|---|
| **Performance** | Bonne | Excellente |
| **Temps réel** | Non | ✅ WebSocket |
| **Mobile** | Limité | ✅ Complet |
| **Multi-user** | ❌ | ✅ |
| **Offline** | Non | ✅ Partial |
| **Customisation** | Limitée | ✅ Complète |
| **Déploiement** | Streamlit Cloud | Docker / Cloud |
| **Coûts** | Gratuit (limited) | Infrastructure |
| **Scalabilité** | Limitée | ✅ Excellente |

## 📝 Checklist Migration

- [ ] Copier la logique `src/` → `backend/services/`
- [ ] Créer les endpoints API pour chaque page
- [ ] Implémenter les modèles Pydantic
- [ ] Migrer la BD (Streamlit → SQLite → PostgreSQL)
- [ ] Créer les sections HTML/CSS
- [ ] Implémenter les appels API JavaScript
- [ ] Tester la synchronisation
- [ ] Optimiser les performances
- [ ] Ajouter l'authentification
- [ ] Déployer en production

## 🔗 Ressources de Migration

### Logique Métier
- `src/analysis_engine.py` → `backend/app/services/analysis_service.py`
- `src/patterns_engine.py` → `backend/app/services/patterns_service.py`
- `src/data_loader.py` → `backend/app/services/data_service.py`

### Données
- `data/*.csv` → Base de données (SQLite)
- `assets/` → `frontend/static/`

### Configuration
- Streamlit config → `.env` + `backend/config.py`

## 🎯 Prochaines Étapes

1. **Phase 1**: Migrer la logique métier existante
2. **Phase 2**: Ajouter l'IA (Groq API)
3. **Phase 3**: Authentification et autorisation
4. **Phase 4**: Déploiement production
5. **Phase 5**: Features avancées (vision, ML)

---

**Dernière mise à jour**: 18 mai 2026
