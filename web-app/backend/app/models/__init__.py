"""
Modèles de données pour TactiCore
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class Match(BaseModel):
    """Modèle pour un match"""
    id: Optional[str] = None
    team_a: str
    team_b: str
    date: datetime
    sport: str = "football"
    status: str = "pending"  # pending, ongoing, completed
    metadata: Dict[str, Any] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "team_a": "Paris FC",
                "team_b": "Lyon",
                "date": "2024-05-18T15:30:00",
                "sport": "football",
                "status": "ongoing"
            }
        }

class ActionAnalysis(BaseModel):
    """Modèle pour l'analyse d'une action"""
    match_id: str
    timestamp: float
    action_type: str
    coordinates: Dict[str, float]
    description: str
    ai_recommendation: Optional[str] = None
    players_involved: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "match_001",
                "timestamp": 1234.5,
                "action_type": "pass",
                "coordinates": {"x": 50, "y": 60},
                "description": "Pass completed",
                "players_involved": ["player_1", "player_2"]
            }
        }

class PerformanceMetrics(BaseModel):
    """Modèle pour les métriques de performance"""
    match_id: str
    team: str
    technical_score: float
    tactical_score: float
    physical_score: float
    mental_score: float
    zones_activity: Dict[str, float]

class SyncEvent(BaseModel):
    """Modèle pour les événements de synchronisation"""
    event_type: str  # match_update, action_added, metrics_updated, etc.
    timestamp: datetime
    data: Dict[str, Any]
    device_id: Optional[str] = None
