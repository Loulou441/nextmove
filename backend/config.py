from dotenv import load_dotenv
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent

# Environment variables win; backend/.env takes precedence over the root
# .env retained for Streamlit. Both paths are independent of the launch cwd.
load_dotenv(BACKEND_DIR / ".env", override=False)
load_dotenv(REPO_ROOT / ".env", override=False)

# API Key for GROQ (peut être absente en mode démo, ne doit pas crasher l'import)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Model name for GROQ (les valeurs par défaut doivent être des modèles Groq valides)
# Modèles Groq (open models hébergés par Groq). "openai/gpt-oss-20b" est le nom
# du modèle open-weights côté Groq — ce n'est PAS un appel à l'API OpenAI.
_DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
MODEL_NAME_PICKELBALL = os.environ.get("MODEL_NAME_PICKELBALL", _DEFAULT_GROQ_MODEL)
MODEL_NAME_TENNIS = os.environ.get("MODEL_NAME_TENNIS", _DEFAULT_GROQ_MODEL)
MODEL_NAME_PADEL = os.environ.get("MODEL_NAME_PADEL", _DEFAULT_GROQ_MODEL)
MODEL_NAME_MODERATOR = os.environ.get("MODEL_NAME_MODERATOR", _DEFAULT_GROQ_MODEL)

# Température des complétions Groq (0.0 = réponses déterministes/reproductibles)
GROQ_TEMPERATURE = float(os.environ.get("GROQ_TEMPERATURE", "0.0"))

# Chemins prompts (calculés depuis l'emplacement de ce fichier : toujours corrects,
# indépendamment de la page Streamlit qui les importe - contrairement à un chemin
# relatif basé sur __file__ d'une page exécutée via exec()).
PROMPT_PATH_PICKELBALL = Path(__file__).resolve().parent / "agents" / "agentpickelball"
PROMPT_PATH_TENNIS = Path(__file__).resolve().parent / "agents" / "agenttennis"
PROMPT_PATH_PADEL = Path(__file__).resolve().parent / "agents" / "agentpadel"
PROMPT_PATH_MODERATOR = Path(__file__).resolve().parent / "agents" / "agentmoderator"

# Accès pratique par clé de sport (utilisé par les pages Streamlit)
PROMPT_PATHS = {
    "pickleball": PROMPT_PATH_PICKELBALL,
    "tennis": PROMPT_PATH_TENNIS,
    "padel": PROMPT_PATH_PADEL,
    "moderator": PROMPT_PATH_MODERATOR,
}

# Personnalisation de l'app (utile pour du white-label / plusieurs déploiements)
APP_PAGE_TITLE = os.environ.get("APP_PAGE_TITLE", "NextMove")
APP_PAGE_ICON = os.environ.get("APP_PAGE_ICON", "🏓")
DEFAULT_SPORT = os.environ.get("DEFAULT_SPORT", "pickleball")

# Origines explicites : nécessaires aux cookies envoyés par le navigateur.
CORS_ORIGINS = [origin.strip().rstrip("/") for origin in os.environ.get(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",") if origin.strip()]
if "*" in CORS_ORIGINS:
    raise ValueError("CORS_ORIGINS doit contenir des origines explicites, pas *")
AUTH_COOKIE_NAME = "access_token"
AUTH_COOKIE_SECURE = os.environ.get("AUTH_COOKIE_SECURE", "false").lower() == "true"
AUTH_COOKIE_SAMESITE = os.environ.get("AUTH_COOKIE_SAMESITE", "lax").lower()
if AUTH_COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise ValueError("AUTH_COOKIE_SAMESITE doit être lax, strict ou none")
if AUTH_COOKIE_SAMESITE == "none" and not AUTH_COOKIE_SECURE:
    raise ValueError("SameSite=None exige AUTH_COOKIE_SECURE=true et HTTPS")
