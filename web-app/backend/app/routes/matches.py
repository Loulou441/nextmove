"""
Endpoints pour la gestion des matchs
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.models import Match, ActionAnalysis, PerformanceMetrics, SyncEvent
from app.services.match_service import MatchService, ActionService, MetricsService
from app.services.sync_service import sync_manager
from datetime import datetime

router = APIRouter(prefix="/api/matches", tags=["matches"])

@router.post("/", response_model=dict)
async def create_match(match: Match):
    """Créer un nouveau match"""
    try:
        match_id = MatchService.create_match(match)
        
        # Diffuser l'événement de création
        await sync_manager.broadcast_update(SyncEvent(
            event_type="match_created",
            timestamp=datetime.now(),
            data={"match_id": match_id, "match": match.dict()}
        ))
        
        return {"id": match_id, "message": "Match créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[dict])
async def get_all_matches():
    """Récupérer tous les matchs"""
    return MatchService.get_all_matches()

@router.get("/{match_id}", response_model=dict)
async def get_match(match_id: str):
    """Récupérer un match spécifique"""
    match = MatchService.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    return match

@router.put("/{match_id}/status", response_model=dict)
async def update_match_status(match_id: str, status: str):
    """Mettre à jour le statut d'un match"""
    if not MatchService.get_match(match_id):
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    MatchService.update_match_status(match_id, status)
    
    # Diffuser la mise à jour
    await sync_manager.broadcast_update(SyncEvent(
        event_type="match_status_updated",
        timestamp=datetime.now(),
        data={"match_id": match_id, "status": status}
    ))
    
    return {"message": f"Statut mis à jour à {status}"}

@router.post("/{match_id}/actions", response_model=dict)
async def add_action(match_id: str, action: ActionAnalysis):
    """Ajouter une action à un match"""
    if not MatchService.get_match(match_id):
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    action.match_id = match_id
    action_id = ActionService.add_action(action)
    
    # Diffuser l'action
    await sync_manager.broadcast_update(SyncEvent(
        event_type="action_added",
        timestamp=datetime.now(),
        data={"match_id": match_id, "action_id": action_id, "action": action.dict()}
    ))
    
    return {"id": action_id, "message": "Action enregistrée"}

@router.get("/{match_id}/actions", response_model=List[dict])
async def get_match_actions(match_id: str):
    """Récupérer les actions d'un match"""
    if not MatchService.get_match(match_id):
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    return ActionService.get_match_actions(match_id)

@router.post("/{match_id}/metrics", response_model=dict)
async def save_metrics(match_id: str, metrics: PerformanceMetrics):
    """Sauvegarder les métriques de performance"""
    if not MatchService.get_match(match_id):
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    metrics.match_id = match_id
    metrics_id = MetricsService.save_metrics(metrics)
    
    # Diffuser les métriques
    await sync_manager.broadcast_update(SyncEvent(
        event_type="metrics_updated",
        timestamp=datetime.now(),
        data={"match_id": match_id, "metrics_id": metrics_id, "metrics": metrics.dict()}
    ))
    
    return {"id": metrics_id, "message": "Métriques enregistrées"}

@router.get("/{match_id}/metrics", response_model=List[dict])
async def get_match_metrics(match_id: str):
    """Récupérer les métriques d'un match"""
    if not MatchService.get_match(match_id):
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    return MetricsService.get_match_metrics(match_id)
