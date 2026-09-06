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


TokenResponse.model_rebuild()
