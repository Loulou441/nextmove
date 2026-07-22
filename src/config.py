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

# Chemins prompts
PROMPT_PATH_PICKELBALL = Path(__file__).resolve().parent / "agents" / "agentpickelball"
PROMPT_PATH_FOOTBALL = Path(__file__).resolve().parent / "agents" / "agentfootball"
PROMPT_PATH_PADEL = Path(__file__).resolve().parent / "agents" / "agentpadel"