"""
Serveur statique simple pour servir le frontend
"""
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

def mount_static_files(app):
    """Monter les fichiers statiques du frontend"""
    frontend_path = Path(__file__).parent.parent / "frontend"
    
    # Monter les fichiers statiques
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
    
    @app.get("/")
    async def root():
        """Servir la page principale"""
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        return {"error": "Frontend not found"}
    
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Favicon (optionnel)"""
        return {"error": "Not found"}

# Exemple d'intégration dans main.py:
# from static_files import mount_static_files
# mount_static_files(app)
