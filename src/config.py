from dotenv import load_dotenv
import os
from pathlib import Path
import re

load_dotenv()

# API Key for GROQ
GROQ_API_KEY=os.environ["GROQ_API_KEY"]

# Model name for GROQ
MODEL_NAME_PICKELBALL=os.environ["MODEL_NAME_PICKELBALL"] if "MODEL_NAME_PICKELBALL" in os.environ else "gpt-4o-mini"
MODEL_NAME_FOOTBALL=os.environ["MODEL_NAME_FOOTBALL"] if "MODEL_NAME_FOOTBALL" in os.environ else "gpt-4o-mini"
MODEL_NAME_PADEL=os.environ["MODEL_NAME_PADEL"] if "MODEL_NAME_PADEL" in os.environ else "gpt-4o-mini"

# Chemins prompts
PROMPT_PATH_PICKELBALL = Path(__file__).resolve().parent / "agents" / "agentpickelball"
PROMPT_PATH_FOOTBALL = Path(__file__).resolve().parent / "agents" / "agentfootball"
PROMPT_PATH_PADEL = Path(__file__).resolve().parent / "agents" / "agentpadel"