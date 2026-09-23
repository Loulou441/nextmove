"""
API HTTP NextMove commune aux clients React et iOS.
Streamlit continue d'utiliser directement ses propres services Python.

Depuis la racine du dépôt :
    python -m uvicorn backend.api.main:app --reload --port 8000
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes_auth import router as auth_router
from backend.api.routes_matches import router as matches_router
from backend.api.routes_coach import router as coach_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_training import router as training_router

app = FastAPI(
    title="NextMove API",
    version="0.1.0",
    description="Backend partagé (auth + données) pour l'app iOS et le web.",
)

# CORS large en développement — l'app iOS et un front web peuvent appeler l'API.
# À restreindre aux domaines réels en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(matches_router)
app.include_router(coach_router)
app.include_router(chat_router)
app.include_router(training_router)

logger = logging.getLogger("nextmove.startup")


@app.on_event("startup")
def preload_rag_models():
    """
    Précharge le modèle d'embeddings et les bases de connaissances (RAG) au
    démarrage du serveur, plutôt qu'à la première requête de chat/coaching —
    évite un délai de ~2 minutes sur le tout premier message d'un utilisateur.
    """
    from backend.config import PROMPT_PATHS
    from backend.agents.agentmanager.rag import get_knowledge_base
    from backend.api.routes_chat import _KNOWLEDGE_FILES

    for sport, filename in _KNOWLEDGE_FILES.items():
        try:
            get_knowledge_base(sport, PROMPT_PATHS[sport] / filename)
            logger.info("Base de connaissances RAG préchargée pour '%s'.", sport)
        except Exception as exc:
            logger.warning("Échec du préchargement RAG pour '%s' : %s", sport, exc)


@app.get("/health", tags=["system"])
def health():
    """Sonde de disponibilité (utile pour un load balancer / un test rapide)."""
    return {"status": "ok"}