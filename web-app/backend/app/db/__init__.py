"""
Gestion de la base de données
"""
import sqlite3
from contextlib import contextmanager
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "tacticore.db"

def init_db():
    """Initialiser la base de données"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des matchs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            team_a TEXT NOT NULL,
            team_b TEXT NOT NULL,
            date TEXT NOT NULL,
            sport TEXT DEFAULT 'football',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table des actions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
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
        )
    """)
    
    # Table des métriques
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id TEXT PRIMARY KEY,
            match_id TEXT NOT NULL,
            team TEXT NOT NULL,
            technical_score REAL,
            tactical_score REAL,
            physical_score REAL,
            mental_score REAL,
            zones_activity TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(match_id) REFERENCES matches(id)
        )
    """)
    
    # Table des événements de synchronisation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            data TEXT NOT NULL,
            device_id TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    """Context manager pour les connexions DB"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
