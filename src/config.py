from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

# API Key for GROQ (peut être absente en mode démo, ne doit pas crasher l'import)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Model name for GROQ (les valeurs par défaut doivent être des modèles Groq valides)
MODEL_NAME_PICKELBALL = os.environ.get("MODEL_NAME_PICKELBALL", "llama-3.3-70b-versatile")
MODEL_NAME_FOOTBALL = os.environ.get("MODEL_NAME_FOOTBALL", "llama-3.3-70b-versatile")
MODEL_NAME_PADEL = os.environ.get("MODEL_NAME_PADEL", "llama-3.3-70b-versatile")

# Température des complétions Groq (0.0 = réponses déterministes/reproductibles)
GROQ_TEMPERATURE = float(os.environ.get("GROQ_TEMPERATURE", "0.0"))

# Chemins prompts (calculés depuis l'emplacement de ce fichier : toujours corrects,
# indépendamment de la page Streamlit qui les importe - contrairement à un chemin
# relatif basé sur __file__ d'une page exécutée via exec()).
PROMPT_PATH_PICKELBALL = Path(__file__).resolve().parent / "agents" / "agentpickelball"
PROMPT_PATH_FOOTBALL = Path(__file__).resolve().parent / "agents" / "agentfootball"
PROMPT_PATH_PADEL = Path(__file__).resolve().parent / "agents" / "agentpadel"

# Accès pratique par clé de sport (utilisé par les pages Streamlit)
PROMPT_PATHS = {
    "pickleball": PROMPT_PATH_PICKELBALL,
    "football": PROMPT_PATH_FOOTBALL,
    "padel": PROMPT_PATH_PADEL,
}

# Dossier de données (surchageable pour pointer vers un autre volume, ex. en conteneur)
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))

# Personnalisation de l'app (utile pour du white-label / plusieurs déploiements)
APP_PAGE_TITLE = os.environ.get("APP_PAGE_TITLE", "NextMove")
APP_PAGE_ICON = os.environ.get("APP_PAGE_ICON", "🏓")
DEFAULT_SPORT = os.environ.get("DEFAULT_SPORT", "pickleball")