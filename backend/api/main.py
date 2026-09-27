"""
API HTTP NextMove commune aux clients React et iOS.
Streamlit continue d'utiliser directement ses propres services Python.

Depuis la racine du dépôt :
    python -m uvicorn backend.api.main:app --reload --port 8000
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from backend.config import CORS_ORIGINS, AUTH_COOKIE_NAME
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes_export import router as export_router
from backend.api.routes_auth import router as auth_router
from backend.api.routes_matches import router as matches_router
from backend.api.routes_coach import router as coach_report_router, coach_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_training import router as training_router

app = FastAPI(
    title="NextMove API",
    version="0.1.0",
    description="Backend partagé (auth + données) pour l'app iOS et le web.",
)

# CORS restreint au frontend web connu. Avec allow_credentials=True (requis
# pour que le cookie httpOnly d'authentification soit envoyé par le
# navigateur), la spécification CORS interdit "*" comme origine — il faut
# lister explicitement les origines autorisées.
# Les domaines de déploiement se configurent via CORS_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def protect_cookie_writes(request: Request, call_next):
    """Les écritures par cookie doivent provenir du frontend autorisé.

    Les clients natifs avec Bearer restent indépendants des cookies/CORS.
    Contrôle aussi l'origine des connexions navigateur (login CSRF).
    """
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        bearer = request.headers.get("authorization", "").lower().startswith("bearer ")
        has_cookie = AUTH_COOKIE_NAME in request.cookies
        auth_action = request.url.path in {"/auth/login", "/auth/register", "/auth/logout"}
        if not bearer and (has_cookie or auth_action):
            allowed = origin in CORS_ORIGINS or origin == str(request.base_url).rstrip("/")
            if (origin and not allowed) or (has_cookie and not origin and not auth_action):
                return JSONResponse(status_code=403, content={"detail": "Origine non autorisée"})
    return await call_next(request)


app.include_router(auth_router)
app.include_router(matches_router)
app.include_router(coach_report_router)   # POST /matches/{id}/coach-report (web)
app.include_router(coach_router)          # POST /coach/recommendations (mobile, RAG-grounded)
app.include_router(chat_router)
app.include_router(training_router)
app.include_router(export_router)
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
