"""
Pipeline de vision par ordinateur — remplace les métriques simulées de
match_service par des mesures dérivées de vraies détections YOLO.

Un modèle YOLO dédié par sport (padel, pickleball, tennis — voir
training/models/exported/) est chargé une seule fois puis réutilisé pour
toutes les analyses. Pour chaque match :

  1. La vidéo est téléchargée depuis Supabase Storage vers un fichier
     temporaire (le stockage ne garde qu'un chemin, pas les octets).
  2. Des frames sont échantillonnées à fréquence fixe (SAMPLE_FPS) et
     passées au détecteur : position de la balle et des joueurs par frame.
  3. Les frames sont regroupées en "rallies" (segments continus de
     présence de balle) ; chaque rally se termine soit par un "winner"
     (accélération nette de la balle juste avant sa disparition) soit par
     une "error" (fin de rally sans accélération notable) — heuristique
     documentée, pas un arbitrage de règles de jeu réel.
  4. La couverture de terrain est calculée comme l'aire de l'enveloppe
     convexe des positions moyennes des joueurs, en pourcentage de la
     surface totale du cadre.

Ce qui est réellement mesuré (rallies, couverture, winners/errors, la
trajectoire de balle) sort de la détection. Ce qui reste hors de portée
d'une détection par boîtes englobantes seules (attribuer un score à un
type de coup précis — service vs volée par ex. — nécessiterait une
estimation de pose) reste une approximation dérivée du score composite
global, documentée comme telle plutôt que présentée comme une mesure
directe.
"""

import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from src.services.video_storage import get_supabase_client, BUCKET_NAME

logger = logging.getLogger("nextmove.cv_pipeline")

# training/ est un dossier frère de streamlit/ à la racine du repo.
# Surchargeable via env (ex: poids montés ailleurs en conteneur), comme
# DATA_DIR dans src/config.py.
_REPO_ROOT = Path(__file__).resolve().parents[3]
WEIGHTS_DIR = Path(os.environ.get("CV_WEIGHTS_DIR", str(_REPO_ROOT / "training" / "models" / "exported")))

_SPORT_WEIGHTS = {
    "padel": WEIGHTS_DIR / "padel_best.pt",
    "pickleball": WEIGHTS_DIR / "pickleball_best.pt",
    "tennis": WEIGHTS_DIR / "tennis_best.pt",
}

# Bornes d'échantillonnage : suffisant pour caractériser une courte séquence
# (usage attendu de l'app, cf. page Upload) sans faire tourner l'inférence
# pendant des minutes sur un long fichier envoyé par erreur.
SAMPLE_FPS = 4.0
MAX_SAMPLED_FRAMES = 200

# Seuils de confiance repris des configs d'entraînement (training/configs/
# *_yolo.yaml, section "Validation") : la balle padel y est documentée comme
# petite et rapide, d'où un seuil plus permissif que pickleball/tennis.
_SPORT_CONF_THRESHOLD = {
    "padel": 0.25,
    "pickleball": 0.3,
    "tennis": 0.3,
}
DEFAULT_CONF_THRESHOLD = 0.3

# Un rally se termine dès que la balle disparaît plus de MAX_GAP_FRAMES
# échantillons de suite (au-delà, on considère que c'est une vraie fin de
# point et pas juste une occlusion courte — cf. README, "Ré-identification
# sur une fenêtre glissante pour gérer les occlusions courtes").
MAX_GAP_FRAMES = 3
MIN_RALLY_FRAMES = 2

_SKILL_TEMPLATES = {
    "pickleball": [("Serve", "🏓"), ("Return", "↩️"), ("Third Shot", "🎯"),
                   ("Dinking", "👆"), ("Volleys", "⚡"), ("Movement", "🚶")],
    "padel": [("Serve", "🎾"), ("Volley", "⚡"), ("Bandeja", "🏓"),
              ("Lob", "🔼"), ("Smash", "💥"), ("Positioning", "📍")],
    "tennis": [("Serve", "🎾"), ("Forehand", "💪"), ("Backhand", "🔄"),
               ("Volley", "⚡"), ("Return", "↩️"), ("Movement", "🚶")],
}

_PHASE_ZONES = {
    # (seuil_x_min, label) — x est la distance normalisée (0-100) au filet
    # (100 = au filet), cohérent avec metriques_video.position_pieds des
    # agents de coaching.
    "pickleball": [(80, "Kitchen"), (55, "Transition"), (0, "Service")],
    "padel": [(70, "Net"), (40, "Transition"), (0, "Baseline")],
    "tennis": [(70, "Net"), (40, "Transition"), (0, "Baseline")],
}

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

_model_cache: dict = {}


class CVPipelineError(Exception):
    """Erreur remontée à l'appelant (affichée telle quelle côté Streamlit)."""


def _load_model(sport: str):
    """Charge (une seule fois, mis en cache) le modèle YOLO du sport donné."""
    if sport in _model_cache:
        return _model_cache[sport]

    weights_path = _SPORT_WEIGHTS.get(sport)
    if weights_path is None:
        raise CVPipelineError(f"Aucun modèle de détection configuré pour le sport '{sport}'.")
    if not weights_path.exists():
        raise CVPipelineError(
            f"Poids introuvables pour '{sport}' : {weights_path}. "
            f"Vérifie training/models/exported/ ou la variable CV_WEIGHTS_DIR."
        )

    # Import différé : ultralytics/torch sont lourds à charger, inutile tant
    # qu'aucune analyse n'a été demandée.
    from ultralytics import YOLO

    logger.info("Chargement du modèle YOLO '%s' depuis %s", sport, weights_path)
    model = YOLO(str(weights_path))
    _model_cache[sport] = model
    return model


def _class_ids_matching(model, keyword: str) -> set:
    """
    Résout les indices de classe dont le nom contient `keyword`, plutôt que
    de figer un indice numérique : l'ordre des classes vient du dataset
    d'entraînement (cf. training/configs/*.yaml) et peut légèrement varier
    d'un export à l'autre — chercher par nom est robuste à ça.
    """
    return {i for i, name in model.names.items() if keyword in name.lower()}


def _download_video(storage_path: str) -> Path:
    """Télécharge la vidéo depuis Supabase Storage vers un fichier temporaire local."""
    client = get_supabase_client()
    try:
        data = client.storage.from_(BUCKET_NAME).download(storage_path)
    except Exception as exc:
        raise CVPipelineError(f"Impossible de récupérer la vidéo depuis le stockage : {exc}") from exc

    suffix = Path(storage_path).suffix or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
    finally:
        tmp.close()
    return Path(tmp.name)


@dataclass
class _FrameDetections:
    t: float  # secondes depuis le début de la vidéo
    ball_xy: Optional[tuple]  # (x, y) normalisé 0-100, ou None si non détectée
    ball_conf: float
    player_xys: list = field(default_factory=list)  # [(x, y), ...] normalisés 0-100


def _sample_and_detect(video_path: Path, model, sport: str) -> tuple[list, float]:
    """Échantillonne la vidéo et fait tourner la détection sur chaque frame retenue."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise CVPipelineError("Vidéo illisible (format non supporté ou fichier corrompu).")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frame_count / fps if fps > 0 else 0.0
        if duration <= 0:
            raise CVPipelineError("Durée de vidéo nulle ou indéterminable.")

        step = 1.0 / SAMPLE_FPS
        n_samples = min(MAX_SAMPLED_FRAMES, max(1, int(duration / step)))
        ball_ids = _class_ids_matching(model, "ball")
        player_ids = _class_ids_matching(model, "player")
        conf_threshold = _SPORT_CONF_THRESHOLD.get(sport, DEFAULT_CONF_THRESHOLD)

        detections: list[_FrameDetections] = []
        for i in range(n_samples):
            t = i * step
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, frame = cap.read()
            if not ok:
                continue

            h, w = frame.shape[:2]
            result = model.predict(frame, conf=conf_threshold, verbose=False)[0]

            best_ball_xy, best_ball_conf = None, -1.0
            player_xys = []
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cx = ((x1 + x2) / 2 / w) * 100
                cy = ((y1 + y2) / 2 / h) * 100
                if cls_id in ball_ids and conf > best_ball_conf:
                    best_ball_xy, best_ball_conf = (cx, cy), conf
                elif cls_id in player_ids:
                    player_xys.append((cx, cy))

            detections.append(_FrameDetections(t=t, ball_xy=best_ball_xy, ball_conf=max(best_ball_conf, 0.0), player_xys=player_xys))
    finally:
        cap.release()

    if not detections:
        raise CVPipelineError("Aucune frame exploitable n'a pu être extraite de la vidéo.")
    return detections, duration


def _segment_rallies(detections: list) -> list:
    """Regroupe les frames en segments continus de présence de balle."""
    segments, current, gap = [], [], 0
    for f in detections:
        if f.ball_xy is not None:
            current.append(f)
            gap = 0
        elif current:
            gap += 1
            if gap > MAX_GAP_FRAMES:
                segments.append(current)
                current, gap = [], 0
    if current:
        segments.append(current)
    return [s for s in segments if len(s) >= MIN_RALLY_FRAMES]


def _ball_speed(a: "_FrameDetections", b: "_FrameDetections") -> float:
    """Vitesse de déplacement de la balle entre deux frames (unités : % de cadre / seconde)."""
    dt = b.t - a.t
    if dt <= 0 or a.ball_xy is None or b.ball_xy is None:
        return 0.0
    dx = b.ball_xy[0] - a.ball_xy[0]
    dy = b.ball_xy[1] - a.ball_xy[1]
    return ((dx ** 2 + dy ** 2) ** 0.5) / dt


def _phase_for_x(x: float, sport: str) -> str:
    zones = _PHASE_ZONES.get(sport, _PHASE_ZONES["pickleball"])
    for threshold, label in zones:
        if x >= threshold:
            return label
    return zones[-1][1]


def _convex_hull_coverage_pct(points: list) -> float:
    """Aire de l'enveloppe convexe des positions joueurs, en % de la surface du cadre."""
    if len(points) < 3:
        return 0.0
    pts = np.array(points, dtype=np.float32)
    hull = cv2.convexHull(pts)
    area = cv2.contourArea(hull)  # en (% de cadre)^2, cadre total = 100*100
    return round(min(100.0, area / 100.0), 1)


@dataclass
class VideoAnalysis:
    rating: float
    rallies: int
    winners: int
    errors: int
    coverage: int
    skills: list
    highlights: list
    insights: list
    patterns_summary: dict
    events: list  # prêts pour persistance en MatchEvent


def analyze_video(sport: str, storage_path: str) -> VideoAnalysis:
    """Point d'entrée : télécharge la vidéo, détecte, agrège les métriques."""
    model = _load_model(sport)
    video_path = _download_video(storage_path)
    try:
        detections, duration = _sample_and_detect(video_path, model, sport)
    finally:
        video_path.unlink(missing_ok=True)

    segments = _segment_rallies(detections)
    if not segments:
        raise CVPipelineError(
            "Aucune balle détectée dans la vidéo — vérifie le cadrage (terrain entier visible) "
            "et la luminosité, ou essaie une séquence différente."
        )

    all_player_xys = [xy for f in detections for xy in f.player_xys]
    all_ball_confs = [f.ball_conf for f in detections if f.ball_xy is not None]
    coverage = _convex_hull_coverage_pct(all_player_xys)
    avg_ball_conf = sum(all_ball_confs) / len(all_ball_confs) if all_ball_confs else 0.0

    events = []
    winners = 0
    errors = 0
    segment_end_speeds = []

    for seg in segments:
        # Vitesse de la balle juste avant la fin du rally : un point qui se
        # termine sur une accélération nette est traité comme un "winner",
        # une fin sans accélération comme une "error" — heuristique de
        # trajectoire, pas un arbitrage réel des règles du jeu.
        end_speed = _ball_speed(seg[-2], seg[-1]) if len(seg) >= 2 else 0.0
        segment_end_speeds.append(end_speed)

        # Événements "SHOT" intermédiaires (positions de balle dans le rally,
        # hors la dernière) pour alimenter compute_match_patterns.
        for f in seg[:-1]:
            events.append({
                "event_type": "SHOT",
                "phase": _phase_for_x(f.ball_xy[0], sport),
                "minute": int(f.t // 60),
                "x": f.ball_xy[0],
                "y": f.ball_xy[1],
            })

        last = seg[-1]
        events.append({
            "event_type": "PENDING",  # rempli juste après (winner/error décidé sur la médiane globale)
            "phase": _phase_for_x(last.ball_xy[0], sport),
            "minute": int(last.t // 60),
            "x": last.ball_xy[0],
            "y": last.ball_xy[1],
            "_end_speed": end_speed,
        })

    median_end_speed = float(np.median(segment_end_speeds)) if segment_end_speeds else 0.0
    for ev in events:
        if ev["event_type"] == "PENDING":
            is_winner = ev.pop("_end_speed") >= median_end_speed
            ev["event_type"] = "WINNER" if is_winner else "ERROR"
            if is_winner:
                winners += 1
            else:
                errors += 1

    rallies = len(segments)
    win_ratio = winners / rallies if rallies > 0 else 0.5
    coverage_norm = min(coverage / 70.0, 1.0)  # 70% de couverture ~ excellent
    rating = round(3.0 + 2.0 * (0.45 * coverage_norm + 0.35 * win_ratio + 0.20 * avg_ball_conf), 1)
    rating = max(1.0, min(5.0, rating))

    skills = _build_skills(sport, rating, coverage_norm)
    highlights = _build_highlights(segments, segment_end_speeds, median_end_speed)
    insights = _INSIGHT_POOL_POSITIVE if rating >= 4.0 else _INSIGHT_POOL_MIXED
    insights = [{"color": c, "text": t} for c, t in insights]

    patterns_summary = _compute_patterns(events, sport)

    return VideoAnalysis(
        rating=rating,
        rallies=rallies,
        winners=winners,
        errors=errors,
        coverage=int(round(coverage)),
        skills=skills,
        highlights=highlights,
        insights=insights,
        patterns_summary=patterns_summary,
        events=events,
    )


def _color_for_score(score: float) -> str:
    if score >= 4.0:
        return "green"
    if score >= 3.0:
        return "blue"
    return "orange"


def _build_skills(sport: str, rating: float, coverage_norm: float) -> list:
    """
    Movement/Positioning est mesuré directement (couverture réelle de
    terrain). Les autres libellés de compétence (type de coup précis) ne
    sont pas discriminables depuis des boîtes englobantes seules — sans
    estimation de pose, on ne peut pas distinguer un service d'une volée.
    Ils héritent donc du score composite global, avec une variation
    déterministe (pas aléatoire) par libellé pour éviter un plafond plat,
    documentée ici plutôt que présentée comme une mesure indépendante.
    """
    templates = _SKILL_TEMPLATES.get(sport, _SKILL_TEMPLATES["pickleball"])
    skills = []
    for idx, (label, icon) in enumerate(templates):
        if label in ("Movement", "Positioning"):
            score = round(3.0 + 2.0 * coverage_norm, 1)
        else:
            # Décalage déterministe (basé sur la position dans la liste, pas
            # sur random) pour ne pas afficher un score strictement identique
            # sur toutes les compétences non mesurées directement.
            offset = ((idx * 37) % 21 - 10) / 20.0  # dans [-0.5, +0.5]
            score = round(max(1.0, min(5.0, rating + offset)), 1)
        skills.append({"label": label, "icon": icon, "score": score, "color": _color_for_score(score)})
    return skills


def _format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _build_highlights(segments: list, end_speeds: list, median_speed: float) -> list:
    """Sélectionne jusqu'à 4 temps forts réels (timestamps issus des détections)."""
    highlights = []

    longest = max(segments, key=len)
    highlights.append({
        "title": "Long rally exchange", "time": _format_timestamp(longest[0].t),
        "tag": "Long rally", "tag_class": "tag-rally",
    })

    winner_idxs = [i for i, s in enumerate(end_speeds) if s >= median_speed]
    if winner_idxs:
        fastest_i = max(winner_idxs, key=lambda i: end_speeds[i])
        seg = segments[fastest_i]
        highlights.append({
            "title": "Powerful winning shot", "time": _format_timestamp(seg[-1].t),
            "tag": "Winner", "tag_class": "tag-winner",
        })

    # Rally où les deux joueurs sont les plus écartés (approximation d'un
    # jeu offensif : un joueur au filet pendant que l'autre couvre le fond).
    def spread(seg):
        pts = [xy for f in seg for xy in f.player_xys]
        if len(pts) < 2:
            return 0.0
        arr = np.array(pts)
        return float(np.max(arr[:, 1]) - np.min(arr[:, 1])) if len(arr) else 0.0

    attacking = max(segments, key=spread, default=None)
    if attacking is not None and spread(attacking) > 0:
        highlights.append({
            "title": "Successful attacking play", "time": _format_timestamp(attacking[0].t),
            "tag": "Attack", "tag_class": "tag-attack",
        })

    error_idxs = [i for i, s in enumerate(end_speeds) if s < median_speed]
    if error_idxs:
        longest_defended_i = max(error_idxs, key=lambda i: len(segments[i]))
        seg = segments[longest_defended_i]
        if len(seg) > MIN_RALLY_FRAMES:
            highlights.append({
                "title": "Strong defensive save", "time": _format_timestamp(seg[0].t),
                "tag": "Great defense", "tag_class": "tag-defense",
            })

    return highlights[:4]


def _compute_patterns(events: list, sport: str) -> dict:
    """
    Synthèse tactique à partir des événements réellement détectés.
    Délègue à src.patterns_engine.compute_match_patterns (la logique
    d'agrégation ne doit exister qu'à un seul endroit — cf. son usage
    identique par la page Patterns pour un match déjà en base).
    """
    import pandas as pd
    from src.patterns_engine import compute_match_patterns

    if not events:
        df = pd.DataFrame(columns=["event_type", "phase", "x"])
    else:
        df = pd.DataFrame(events)
    return compute_match_patterns(df, sport=sport)
