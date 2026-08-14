"""
Modèles SQLAlchemy — schéma complet de la base de données NextMove.

Pensé pour couvrir l'ensemble de l'app existante (Library, Dashboard,
AI Analysis, Patterns, Training Plan), pas seulement l'authentification,
pour éviter de refaire des migrations à chaque nouvelle fonctionnalité.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    preferred_sport = Column(String(50), default="pickleball")
    created_at = Column(DateTime, default=datetime.utcnow)

    matches = relationship("Match", back_populates="user", cascade="all, delete-orphan")
    training_plans = relationship("TrainingPlan", back_populates="user", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    sport = Column(String(50), nullable=False)  # pickleball / football / padel
    match_date = Column(DateTime, nullable=True)
    duration = Column(String(20), nullable=True)  # ex. "4:22"
    status = Column(String(20), default="pending")  # pending / ready
    rating = Column(Float, nullable=True)

    rallies = Column(Integer, nullable=True)
    winners = Column(Integer, nullable=True)
    errors = Column(Integer, nullable=True)
    coverage = Column(Integer, nullable=True)

    video_storage_path = Column(String(500), nullable=True)  # chemin dans le bucket Supabase Storage
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="matches")
    events = relationship("MatchEvent", back_populates="match", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="match", cascade="all, delete-orphan")
    patterns = relationship("Pattern", back_populates="match", cascade="all, delete-orphan")


class MatchEvent(Base):
    """Un événement/point du match — future sortie de l'extraction vidéo (YOLOv8)."""
    __tablename__ = "match_events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    match_id = Column(UUID(as_uuid=False), ForeignKey("matches.id"), nullable=False, index=True)

    event_type = Column(String(50), nullable=True)
    phase = Column(String(50), nullable=True)
    minute = Column(Integer, nullable=True)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    raw_data = Column(JSON, nullable=True)  # flexibilité pour données brutes futures (tracking...)

    match = relationship("Match", back_populates="events")


class Analysis(Base):
    """Rapport de coaching IA généré pour un événement précis d'un match."""
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    match_id = Column(UUID(as_uuid=False), ForeignKey("matches.id"), nullable=False, index=True)

    individual_pct = Column(Integer, nullable=True)
    collective_pct = Column(Integer, nullable=True)
    tactical_pct = Column(Integer, nullable=True)
    explanation = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)  # liste de strings
    confidence = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="analyses")


class Pattern(Base):
    """Tendance récurrente détectée dans le jeu (page Patterns)."""
    __tablename__ = "patterns"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    match_id = Column(UUID(as_uuid=False), ForeignKey("matches.id"), nullable=False, index=True)

    pattern_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="patterns")


class TrainingPlan(Base):
    """Programme d'entraînement hebdomadaire généré par l'IA."""
    __tablename__ = "training_plans"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)

    sport = Column(String(50), nullable=False)
    content = Column(JSON, nullable=True)  # structure du plan (jours, exercices...)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="training_plans")