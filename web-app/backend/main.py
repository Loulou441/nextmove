"""
Point d'entrée de l'application FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# Imports des routes
from app.routes import matches, sync
from app.db import init_db

# Créer l'application FastAPI
app = FastAPI(
    title="TactiCore API",
    description="API d'analyse sportive intelligente avec synchronisation en temps réel",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la base de données
init_db()

# Inclure les routes
app.include_router(matches.router)
app.include_router(sync.router)

# Route de base
@app.get("/")
async def root():
    """Endpoint de santé"""
    return {
        "message": "TactiCore API est actif",
        "version": "1.0.0",
        "endpoints": {
            "matches": "/api/matches",
            "sync": "/api/sync",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Vérifier la santé de l'API"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
