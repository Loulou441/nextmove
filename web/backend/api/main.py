"""
Point d'entrée de l'API REST NextMove (FastAPI).

Cette API expose l'authentification et les données déjà gérées par
l'application web (mêmes modèles, même base, mêmes tokens JWT) à des clients
externes — en premier lieu l'application iOS. Le web (Streamlit) et l'API
partagent donc le MÊME backend : un compte créé d'un côté fonctionne de l'autre.

Lancement en local :
    uvicorn src.api.main:app --reload --port 8000
Documentation interactive :
    http://localhost:8000/docs
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_auth import router as auth_router
from api.routes_matches import router as matches_router
from api.routes_coach import router as coach_router
from api.routes_chat import router as chat_router
from api.routes_training import router as training_router

app = FastAPI(
    title="NextMove API",
    version="0.1.0",
    description="Backend partagé (auth + données) pour l'app iOS et le web.",
)

# CORS restreint au frontend web connu. Avec allow_credentials=True (requis
# pour que le cookie httpOnly d'authentification soit envoyé par le
# navigateur), la spécification CORS interdit "*" comme origine — il faut
# lister explicitement les origines autorisées.
# TODO: ajouter ici le vrai domaine de production une fois déployé.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
    from config import PROMPT_PATHS
    from agents.agentmanager.rag import get_knowledge_base
    from api.routes_chat import _KNOWLEDGE_FILES

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