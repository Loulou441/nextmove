"""
TactiCore Backend API - Application principale
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

def create_app():
    """Créer et configurer l'application FastAPI"""
    app = FastAPI(
        title="TactiCore API",
        description="API d'analyse sportive intelligente",
        version="1.0.0"
    )
    
    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app
