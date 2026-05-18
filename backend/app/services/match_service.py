"""
Service pour la gestion des matchs
"""
import uuid
import json
from datetime import datetime
from typing import List, Optional
from app.db import get_db
from app.models import Match, ActionAnalysis, PerformanceMetrics

class MatchService:
    """Service pour les opérations sur les matchs"""
    
    @staticmethod
    def create_match(match: Match) -> str:
        """Créer un nouveau match"""
        match_id = str(uuid.uuid4())
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO matches (id, team_a, team_b, date, sport, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (match_id, match.team_a, match.team_b, match.date.isoformat(), 
                  match.sport, match.status))
            conn.commit()
        
        return match_id
    
    @staticmethod
    def get_match(match_id: str) -> Optional[dict]:
        """Récupérer un match"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
            result = cursor.fetchone()
        
        if result:
            return dict(result)
        return None
    
    @staticmethod
    def get_all_matches() -> List[dict]:
        """Récupérer tous les matchs"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM matches ORDER BY date DESC")
            results = cursor.fetchall()
        
        return [dict(row) for row in results]
    
    @staticmethod
    def update_match_status(match_id: str, status: str) -> bool:
        """Mettre à jour le statut d'un match"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE matches 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, match_id))
            conn.commit()
        
        return True

class ActionService:
    """Service pour la gestion des actions"""
    
    @staticmethod
    def add_action(action: ActionAnalysis) -> str:
        """Ajouter une nouvelle action"""
        action_id = str(uuid.uuid4())
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO actions 
                (id, match_id, timestamp, action_type, coordinates_x, 
                 coordinates_y, description, ai_recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (action_id, action.match_id, action.timestamp, action.action_type,
                  action.coordinates.get("x"), action.coordinates.get("y"),
                  action.description, action.ai_recommendation))
            conn.commit()
        
        return action_id
    
    @staticmethod
    def get_match_actions(match_id: str) -> List[dict]:
        """Récupérer les actions d'un match"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM actions 
                WHERE match_id = ? 
                ORDER BY timestamp ASC
            """, (match_id,))
            results = cursor.fetchall()
        
        return [dict(row) for row in results]

class MetricsService:
    """Service pour les métriques de performance"""
    
    @staticmethod
    def save_metrics(metrics: PerformanceMetrics) -> str:
        """Sauvegarder les métriques"""
        metrics_id = str(uuid.uuid4())
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics
                (id, match_id, team, technical_score, tactical_score, 
                 physical_score, mental_score, zones_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (metrics_id, metrics.match_id, metrics.team,
                  metrics.technical_score, metrics.tactical_score,
                  metrics.physical_score, metrics.mental_score,
                  json.dumps(metrics.zones_activity)))
            conn.commit()
        
        return metrics_id
    
    @staticmethod
    def get_match_metrics(match_id: str) -> List[dict]:
        """Récupérer les métriques d'un match"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM performance_metrics 
                WHERE match_id = ?
            """, (match_id,))
            results = cursor.fetchall()
        
        data = []
        for row in results:
            row_dict = dict(row)
            if row_dict.get("zones_activity"):
                row_dict["zones_activity"] = json.loads(row_dict["zones_activity"])
            data.append(row_dict)
        
        return data
