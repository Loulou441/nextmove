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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes_auth import router as auth_router
from src.api.routes_matches import router as matches_router

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


@app.get("/health", tags=["system"])
def health():
    """Sonde de disponibilité (utile pour un load balancer / un test rapide)."""
    return {"status": "ok"}
