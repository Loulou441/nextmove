"""
Schémas Pydantic de l'API REST — contrats d'entrée/sortie HTTP.

Ils convertissent les modèles SQLAlchemy (src/db/models.py) en JSON propre
pour les clients (application iOS, et plus tard tout autre client), sans
jamais exposer le hash du mot de passe.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ---------- Authentification ----------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Mot de passe en clair (min. 6 caractères)")
    preferred_sport: str = "pickleball"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    preferred_sport: str

class TokenResponse(BaseModel):
    """Réponse renvoyée après une connexion/inscription réussie."""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    preferred_sport: str
    created_at: datetime

    class Config:
        from_attributes = True  # permet UserResponse.model_validate(user_sqlalchemy)


# ---------- Matchs ----------

class MatchResponse(BaseModel):
    id: str
    title: str
    sport: str
    status: str
    match_date: datetime | None = None
    duration: str | None = None
    rating: float | None = None
    rallies: int | None = None
    winners: int | None = None
    errors: int | None = None
    coverage: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MatchSyncRequest(BaseModel):
    """
    Payload envoyé par l'app mobile après une analyse locale (Core ML).
    Permet de sauvegarder le résultat dans la base partagée pour qu'il
    apparaisse aussi sur le web.
    """
    title: str
    sport: str
    duration: str | None = None
    rallies: int | None = None
    winners: int | None = None
    errors: int | None = None
    coverage: int | None = None
    rating: float | None = None
    skills: list | None = None
    highlights: list | None = None
    insights: list | None = None
    patterns_summary: dict | None = None


class MatchDetailResponse(BaseModel):
    """Version complète d'un match, avec le détail du dashboard (skills,
    highlights, insights, résumé de patterns) — utilisée par GET /matches/{id}."""
    id: str
    title: str
    sport: str
    status: str
    match_date: datetime | None = None
    duration: str | None = None
    rating: float | None = None
    rallies: int | None = None
    winners: int | None = None
    errors: int | None = None
    coverage: int | None = None
    skills: list | None = None
    highlights: list | None = None
    insights: list | None = None
    patterns_summary: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MatchEventResponse(BaseModel):
    """Un événement détecté automatiquement lors de l'analyse vidéo
    (winner, error, shot) — utilisé pour peupler le sélecteur du Coach Chat."""
    id: str
    event_type: str | None = None
    phase: str | None = None
    minute: int | None = None
    x: float | None = None
    y: float | None = None

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
TokenResponse.model_rebuild()


# ---------- Coach IA (agents RAG) ----------

class CoachSequenceInput(BaseModel):
    """Une séquence de jeu à analyser par le coach RAG.

    Les clients (iOS) envoient des séquences dérivées de leur analyse locale
    (highlights, événements). Les champs correspondent au format attendu par
    les agents RAG (`donnees_sequences`).
    """
    timestamp: str = ""
    evenement_cle: str = Field(default="", description="Événement clé de la séquence")
    contexte_tactique: str = Field(default="", description="Contexte tactique")
    metriques_video: dict = Field(default_factory=dict)


class CoachRecommendationsRequest(BaseModel):
    """Requête iOS/web pour obtenir des recommandations du coach RAG."""
    sport: str = Field(description="pickleball | padel | tennis")
    sequences: list[CoachSequenceInput] = Field(
        default_factory=list,
        description="Séquences de jeu à coacher (au moins une).",
    )
    joueur: dict = Field(default_factory=dict, description="Infos joueur optionnelles (nom, position…).")


class CoachRecommendationContent(BaseModel):
    constat: str
    analyse: str
    action_corrective: str
    pro_tip: str | None = None
    exercice_source_id: str | None = None


class CoachRecommendation(BaseModel):
    timestamp: str
    titre: str
    contenu: CoachRecommendationContent


class CoachRecommendationsResponse(BaseModel):
    """Réponse structurée du coach RAG (miroir de RecommandationsCoach)."""
    sport: str
    recommandations_coach: list[CoachRecommendation]
