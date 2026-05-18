"""
Configuration de l'application backend
"""
import os
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "tacticore.db"

# Configuration CORS
CORS_ORIGINS = ["*"]

# Configuration API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_RELOAD = os.getenv("API_RELOAD", "True") == "True"

# Configuration Groq (pour l'IA)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Configuration des limites
MAX_ACTIONS_PER_MATCH = 1000
MAX_METRICS_PER_MATCH = 100
