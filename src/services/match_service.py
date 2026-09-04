"""
Service métier pour les matchs (Match) — création à l'upload, mise à
jour du statut/métriques après l'étape d'analyse.
"""

import random
from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Match

# ── Pools utilisés pour simuler l'analyse (en attendant YOLOv8) ───────
_SKILL_TEMPLATES = {
    "pickleball": [("Serve", "🏓"), ("Return", "↩️"), ("Third Shot", "🎯"),
                   ("Dinking", "👆"), ("Volleys", "⚡"), ("Movement", "🚶")],
    "football": [("Passing", "⚽"), ("Shooting", "🎯"), ("Dribbling", "🏃"),
                 ("Positioning", "📍"), ("Tackling", "🛡️"), ("Stamina", "💨")],
    "padel": [("Serve", "🎾"), ("Volley", "⚡"), ("Bandeja", "🏓"),
              ("Lob", "🔼"), ("Smash", "💥"), ("Positioning", "📍")],
}

_HIGHLIGHT_TEMPLATES = [
    ("Powerful winning shot", "Winner", "tag-winner"),
    ("Long rally exchange", "Long rally", "tag-rally"),
    ("Successful attacking play", "Attack", "tag-attack"),
    ("Strong defensive save", "Great defense", "tag-defense"),
]

_INSIGHT_POOL_POSITIVE = [
    ("#34C759", "Strong overall performance"),
    ("#34C759", "Consistent execution throughout"),
    ("#007AFF", "Good court/field coverage"),
]
_INSIGHT_POOL_MIXED = [
    ("#FF9500", "Some inconsistency in key moments"),
    ("#FF3B30", "A few unforced errors to work on"),
    ("#007AFF", "Movement stayed solid throughout"),
]


def _color_for_score(score: float) -> str:
    if score >= 4.0:
        return "green"
    if score >= 3.0:
        return "blue"
    return "orange"


def _generate_analysis_content(sport: str, rating: float) -> tuple[list, list, list]:
    """
    Génère skills/highlights/insights simulés pour un match.

    ⚠️ SIMULÉ — en attendant le vrai pipeline YOLOv8 d'extraction vidéo
    (cf. README du POC). Le jour où YOLOv8 sera branché, seule cette
    fonction change : elle retournera des valeurs calculées depuis la
    vidéo plutôt que tirées aléatoirement. Rien d'autre dans l'app n'a
    besoin de changer, puisque Dashboard lit déjà ces champs depuis la BDD.
    """
    templates = _SKILL_TEMPLATES.get(sport, _SKILL_TEMPLATES["pickleball"])
    skills = []
    for label, icon in templates:
        score = round(random.uniform(3.0, 5.0), 1)
        skills.append({"label": label, "icon": icon, "score": score, "color": _color_for_score(score)})

    highlights = []
    for title, tag, tag_class in random.sample(_HIGHLIGHT_TEMPLATES, k=min(4, len(_HIGHLIGHT_TEMPLATES))):
        minute = random.randint(0, 8)
        second = random.randint(0, 59)
        highlights.append({"title": title, "time": f"{minute}:{second:02d}", "tag": tag, "tag_class": tag_class})

    insight_pool = _INSIGHT_POOL_POSITIVE if rating >= 4.0 else _INSIGHT_POOL_MIXED
    insights = [{"color": c, "text": t} for c, t in insight_pool]

    return skills, highlights, insights


_PHASE_TEMPLATES = {
    "pickleball": ["Kitchen", "Transition", "Service"],
    "football": ["Build-up", "Transition", "Final Third"],
    "padel": ["Net", "Baseline", "Transition"],
}
_ZONE_TEMPLATES = {
    "pickleball": ["Zone du filet (Kitchen)", "Zone de transition avant", "Zone médiane", "Zone de fond de court (service)"],
    "football": ["Zone défensive", "Zone médiane", "Zone offensive", "Couloirs"],
    "padel": ["Zone du filet", "Zone médiane", "Zone de fond de court", "Couloirs latéraux"],
}


def _generate_patterns_summary(sport: str, rallies: int, winners: int, errors: int) -> dict:
    """
    Génère un résumé de patterns tactiques simulé pour un match.

    ⚠️ SIMULÉ — en attendant que match_events soit alimentée par le vrai
    pipeline YOLOv8 (actuellement une table vide, prévue pour ça). Une fois
    branché, ce résumé pourra être recalculé depuis les vrais événements
    (cf. src/patterns_engine.py, compute_match_patterns) au lieu d'être
    tiré aléatoirement — la page Patterns n'aura rien à changer.
    """
    total_events = rallies + winners + errors
    total_shots = max(1, rallies - winners - errors)

    phases = _PHASE_TEMPLATES.get(sport, _PHASE_TEMPLATES["pickleball"])
    phase_weights = [random.randint(3, 12) for _ in phases]
    phase_distribution = dict(zip(phases, phase_weights))

    zones = _ZONE_TEMPLATES.get(sport, _ZONE_TEMPLATES["pickleball"])
    zone_weights = [random.randint(2, 10) for _ in zones]
    zone_distribution = dict(zip(zones, zone_weights))

    transition_risk_ratio = round(errors / total_events, 2) if total_events > 0 else 0.0
    if transition_risk_ratio >= 0.35:
        priority_level = "Élevée"
    elif transition_risk_ratio >= 0.20:
        priority_level = "Moyenne"
    else:
        priority_level = "Faible"

    top_zone = max(zone_distribution, key=zone_distribution.get)
    insights = [f"Volume élevé d'échanges dans la zone : {top_zone}."]
    if errors >= 8:
        insights.append("Nombre important d'erreurs non forcées potentiellement évitables.")
    else:
        insights.append("Bon contrôle global, peu d'erreurs non forcées.")

    return {
        "total_events": total_events,
        "total_winners": winners,
        "total_shots": total_shots,
        "total_errors": errors,
        "phase_distribution": phase_distribution,
        "zone_distribution": zone_distribution,
        "transition_risk_ratio": transition_risk_ratio,
        "priority_level": priority_level,
        "insights": insights,
    }


def create_pending_match(
    db: Session,
    user_id: str,
    title: str,
    sport: str,
    video_storage_path: str,
) -> Match:
    """Crée un match en attente d'analyse, juste après l'upload de la vidéo."""
    match = Match(
        user_id=user_id,
        title=title,
        sport=sport,
        match_date=datetime.utcnow(),
        status="pending",
        video_storage_path=video_storage_path,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def mark_match_ready(db: Session, match_id: str) -> Match:
    """
    Marque un match comme analysé, avec des métriques et un détail par
    compétence/highlight/insight.

    Pour l'instant tout est simulé (le vrai pipeline YOLOv8 n'existe pas
    encore) — mais contrairement à avant, c'est réellement écrit en BDD,
    pas juste affiché. Quand YOLOv8 sera branché, seul le contenu de
    cette fonction changera : les métriques viendront de l'extraction
    vidéo au lieu d'être tirées aléatoirement, sans toucher au reste
    de l'app.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise ValueError(f"Match {match_id} introuvable")

    match.status = "ready"
    match.rating = round(random.uniform(3.2, 4.8), 1)
    match.rallies = random.randint(20, 60)
    match.winners = random.randint(5, 20)
    match.errors = random.randint(3, 15)
    match.coverage = random.randint(60, 95)

    skills, highlights, insights = _generate_analysis_content(match.sport, match.rating)
    match.skills = skills
    match.highlights = highlights
    match.insights = insights
    match.patterns_summary = _generate_patterns_summary(match.sport, match.rallies, match.winners, match.errors)

    db.commit()
    db.refresh(match)
    return match


def get_user_matches(db: Session, user_id: str) -> list[Match]:
    """Retourne tous les matchs d'un utilisateur, les plus récents d'abord."""
    return (
        db.query(Match)
        .filter(Match.user_id == user_id)
        .order_by(Match.created_at.desc())
        .all()
    )