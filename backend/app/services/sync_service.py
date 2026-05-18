"""
Service de synchronisation en temps réel
"""
import json
import uuid
from datetime import datetime
from typing import Set, Dict, Any
from app.db import get_db
from app.models import SyncEvent

class SyncManager:
    """Gestionnaire de synchronisation avec WebSockets"""
    
    def __init__(self):
        self.connected_clients: Set[str] = set()
        self.sync_queue: Dict[str, list] = {}
    
    async def connect(self, device_id: str):
        """Enregistrer un client connecté"""
        self.connected_clients.add(device_id)
        if device_id not in self.sync_queue:
            self.sync_queue[device_id] = []
    
    async def disconnect(self, device_id: str):
        """Désenregistrer un client"""
        self.connected_clients.discard(device_id)
    
    async def broadcast_update(self, event: SyncEvent):
        """Diffuser une mise à jour à tous les clients"""
        # Sauvegarder l'événement en BD
        self._save_sync_event(event)
        
        # Diffuser à tous les clients
        for client_id in self.connected_clients:
            if client_id not in self.sync_queue:
                self.sync_queue[client_id] = []
            self.sync_queue[client_id].append(event.dict())
    
    async def get_pending_updates(self, device_id: str) -> list:
        """Récupérer les mises à jour en attente"""
        updates = self.sync_queue.get(device_id, [])
        self.sync_queue[device_id] = []
        return updates
    
    @staticmethod
    def _save_sync_event(event: SyncEvent):
        """Sauvegarder un événement de sync en BD"""
        event_id = str(uuid.uuid4())
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_events (id, event_type, data, device_id, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (event_id, event.event_type, json.dumps(event.data), 
                  event.device_id, event.timestamp.isoformat()))
            conn.commit()

# Instance globale
sync_manager = SyncManager()
