"""
Endpoints WebSocket et polling pour la synchronisation en temps réel
"""
from fastapi import APIRouter, WebSocket, HTTPException
from app.services.sync_service import sync_manager
import json

router = APIRouter(prefix="/api/sync", tags=["sync"])

@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket endpoint pour la synchronisation en temps réel"""
    await websocket.accept()
    await sync_manager.connect(device_id)
    
    try:
        while True:
            # Recevoir les messages du client
            data = await websocket.receive_text()
            
            # Traiter les messages si nécessaire
            # Pour l'instant, simplement écouter
            
            # Envoyer les mises à jour en attente
            updates = await sync_manager.get_pending_updates(device_id)
            if updates:
                await websocket.send_json({"type": "updates", "data": updates})
    
    except Exception as e:
        await sync_manager.disconnect(device_id)

@router.get("/updates/{device_id}")
async def get_updates(device_id: str):
    """Polling endpoint pour récupérer les mises à jour"""
    updates = await sync_manager.get_pending_updates(device_id)
    return {"updates": updates}

@router.post("/register/{device_id}")
async def register_device(device_id: str):
    """Enregistrer un device"""
    await sync_manager.connect(device_id)
    return {"message": f"Device {device_id} enregistré"}

@router.post("/unregister/{device_id}")
async def unregister_device(device_id: str):
    """Désenregistrer un device"""
    await sync_manager.disconnect(device_id)
    return {"message": f"Device {device_id} désenregistré"}
