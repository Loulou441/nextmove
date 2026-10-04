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
  3. Les détections de balle sont regroupées en trajectoires (services/
     ios_tracker.py, aligné sur le suivi de l'app iOS), puis les
     trajectoires en points (services/rally_builder.py) : deux coups
     appartiennent au même point s'ils sont proches dans le temps ET
     alternent de sens (vers le filet, puis vers le fond) — un vrai
     échange, pas une balle qui continue de rouler dans le même sens.
  4. Chaque compétence (services/skill_scoring.py) est la qualité moyenne
     des coups qui correspondent à son critère (position dans le point,
     zone du terrain, vitesse), plutôt qu'un décalage arbitraire autour de
     la note globale. Une compétence sans coup correspondant sur ce match
     n'est pas affichée avec une valeur inventée : elle est absente.
  5. Winner/erreur reste une heuristique documentée (vitesse du dernier
     coup du point comparée à la médiane du match), pas un arbitrage réel
     des règles du jeu — appliquée désormais à un vrai découpage en points
     plutôt qu'à un simple fragment continu de détection.
  6. La couverture de terrain est calculée comme l'aire de l'enveloppe
     convexe des positions des joueurs, en pourcentage de la surface
     totale du cadre.

Les seuils utilisés (écart de temps entre coups, vitesse lente/rapide) sont
des choix raisonnables, non calibrés sur des données réelles — à ajuster
une fois validés sur le terrain.
"""

import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from backend.services.video_storage import get_supabase_client, BUCKET_NAME
from backend.services.ios_tracker import Detection as _TrackDetection, ball_trajectories, track_detections
from backend.services.rally_builder import build_points
from backend.services.shot_metrics import shot_speed
from backend.services.player_selection import build_player_payloads
from backend.services import skill_scoring as sk

logger = logging.getLogger("nextmove.cv_pipeline")

# Les poids partagés restent dans training/ à la racine du dépôt.
# Surchargeable via env (ex: poids montés ailleurs en conteneur).
from backend.config import REPO_ROOT as _REPO_ROOT
WEIGHTS_DIR = Path(os.environ.get("CV_WEIGHTS_DIR", str(_REPO_ROOT / "training" / "models" / "exported")))

_SPORT_WEIGHTS = {
    "padel": WEIGHTS_DIR / "padel_best.pt",
    "pickleball": WEIGHTS_DIR / "pickleball_best.pt",
    "tennis": WEIGHTS_DIR / "tennis_best.pt",
}

SAMPLE_FPS = 5.0
MAX_SAMPLED_FRAMES = 300

_SPORT_CONF_THRESHOLD = {
    "padel": 0.25,
    "pickleball": 0.3,
    "tennis": 0.3,
}
DEFAULT_CONF_THRESHOLD = 0.3

_SKILL_TEMPLATES = {
    "pickleball": [("Serve", "Zap"), ("Return", "RotateCcw"), ("Third Shot", "Crosshair"),
                   ("Dinking", "MousePointer2"), ("Volleys", "Target"), ("Movement", "Move")],
    "padel": [("Serve", "Zap"), ("Volley", "Target"), ("Défense", "Shield"),
              ("Lob", "ArrowUp"), ("Smash", "Zap"), ("Positioning", "Move")],
    "tennis": [("Serve", "Zap"), ("Fond de court", "TrendingUp"), ("Régularité", "Repeat"),
               ("Volley", "Target"), ("Return", "RotateCcw"), ("Movement", "Move")],
}

_PHASE_ZONES = {
    "pickleball": [(80, "Kitchen"), (55, "Transition"), (0, "Service")],
    "padel": [(70, "Net"), (40, "Transition"), (0, "Baseline")],
    "tennis": [(70, "Net"), (40, "Transition"), (0, "Baseline")],
}

_INSIGHT_POOL_POSITIVE = [
    ("#34C759", "Performance globale solide"),
    ("#34C759", "Exécution régulière tout au long du match"),
    ("#007AFF", "Bonne couverture du terrain"),
]
_INSIGHT_POOL_MIXED = [
    ("#FF9500", "Quelques irrégularités dans les moments clés"),
    ("#FF3B30", "Quelques erreurs évitables à travailler"),
    ("#007AFF", "Déplacements restés solides tout du long"),
]

_model_cache: dict = {}


class CVPipelineError(Exception):
    """Erreur remontée à l'appelant (affichée telle quelle côté Streamlit)."""


def _load_model(sport: str):
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

    from ultralytics import YOLO

    logger.info("Chargement du modèle YOLO '%s' depuis %s", sport, weights_path)
    model = YOLO(str(weights_path))
    _model_cache[sport] = model
    return model


def _class_ids_matching(model, keyword: str) -> set:
    return {i for i, name in model.names.items() if keyword in name.lower()}


def _download_video(storage_path: str) -> Path:
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
    t: float
    ball_xy: Optional[tuple]
    ball_conf: float
    player_xys: list = field(default_factory=list)
    track_inputs: list = field(default_factory=list)


def _sample_and_detect(video_path: Path, model, sport: str) -> tuple[list, float]:
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
            track_inputs = []
            frame_index = len(detections)
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

                if cls_id in ball_ids:
                    track_cls = "ball"
                elif cls_id in player_ids:
                    track_cls = "player"
                else:
                    continue
                track_inputs.append(_TrackDetection(
                    frame=frame_index, cls=track_cls,
                    box=(x1 / w, y1 / h, x2 / w, y2 / h),
                    confidence=conf, t=t,
                ))

            detections.append(_FrameDetections(
                t=t, ball_xy=best_ball_xy, ball_conf=max(best_ball_conf, 0.0),
                player_xys=player_xys, track_inputs=track_inputs,
            ))
    finally:
        cap.release()

    if not detections:
        raise CVPipelineError("Aucune frame exploitable n'a pu être extraite de la vidéo.")
    return detections, duration


def _phase_for_x(x: float, sport: str) -> str:
    zones = _PHASE_ZONES.get(sport, _PHASE_ZONES["pickleball"])
    for threshold, label in zones:
        if x >= threshold:
            return label
    return zones[-1][1]


def _convex_hull_coverage_pct(points: list) -> float:
    if len(points) < 3:
        return 0.0
    pts = np.array(points, dtype=np.float32)
    hull = cv2.convexHull(pts)
    area = cv2.contourArea(hull)
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
    events: list
    players: list = field(default_factory=list)


def analyze_video(sport: str, storage_path: str) -> VideoAnalysis:
    model = _load_model(sport)
    video_path = _download_video(storage_path)
    try:
        detections, duration = _sample_and_detect(video_path, model, sport)
        # Les vignettes se recadrent dans la vidéo : à faire avant sa suppression.
        players = build_player_payloads(video_path, [d for f in detections for d in f.track_inputs])
    finally:
        video_path.unlink(missing_ok=True)

    all_inputs = [d for f in detections for d in f.track_inputs]
    frame_times = {d.frame: d.t for d in all_inputs}
    trajectories = ball_trajectories(track_detections(all_inputs))

    if not trajectories:
        raise CVPipelineError(
            "Aucune balle détectée dans la vidéo — vérifie le cadrage (terrain entier visible) "
            "et la luminosité, ou essaie une séquence différente."
        )

    points = build_points(trajectories, frame_times.get)
    all_shots = [shot for point in points for shot in point]

    all_player_xys = [xy for f in detections for xy in f.player_xys]
    all_ball_confs = [f.ball_conf for f in detections if f.ball_xy is not None]
    coverage = _convex_hull_coverage_pct(all_player_xys)
    avg_ball_conf = sum(all_ball_confs) / len(all_ball_confs) if all_ball_confs else 0.0

    point_end_speeds = [shot_speed(point[-1]) for point in points]
    median_end_speed = float(np.median(point_end_speeds)) if point_end_speeds else 0.0

    events = []
    winners = 0
    errors = 0
    for point, end_speed in zip(points, point_end_speeds):
        for shot in point[:-1]:
            x_end = shot.trajectory.trajectory[-1][0] * 100
            y_end = shot.trajectory.trajectory[-1][1] * 100
            events.append({
                "event_type": "SHOT",
                "phase": _phase_for_x(x_end, sport),
                "minute": int(shot.start_t // 60),
                "x": x_end,
                "y": y_end,
            })

        last = point[-1]
        x_end = last.trajectory.trajectory[-1][0] * 100
        y_end = last.trajectory.trajectory[-1][1] * 100
        is_winner = end_speed >= median_end_speed
        events.append({
            "event_type": "WINNER" if is_winner else "ERROR",
            "phase": _phase_for_x(x_end, sport),
            "minute": int(last.start_t // 60),
            "x": x_end,
            "y": y_end,
        })
        if is_winner:
            winners += 1
        else:
            errors += 1

    rallies = len(points)
    win_ratio = winners / rallies if rallies > 0 else 0.5
    coverage_norm = min(coverage / 70.0, 1.0)
    rating = round(3.0 + 2.0 * (0.45 * coverage_norm + 0.35 * win_ratio + 0.20 * avg_ball_conf), 1)
    rating = max(1.0, min(5.0, rating))

    skills = _build_skills(sport, points, all_shots, coverage_norm)
    highlights = _build_highlights(points, detections, point_end_speeds, median_end_speed)
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
        players=players,
    )


def _color_for_score(score: float) -> str:
    if score >= 4.0:
        return "green"
    if score >= 3.0:
        return "blue"
    return "orange"


def _build_skills(sport: str, points: list, all_shots: list, coverage_norm: float) -> list:
    movement_score = round(3.0 + 2.0 * coverage_norm, 1)

    if sport == "pickleball":
        net_zone = sk.NET_ZONE[sport]
        raw = [
            ("Serve", "serve", sk.skill_by_shot_index(points, 0)),
            ("Return", "return", sk.skill_by_shot_index(points, 1)),
            ("Third Shot", "thirdShot", sk.skill_by_shot_index(points, 2)),
            ("Dinking", "dinking", sk.skill_dinking(all_shots, _phase_for_x, sport)),
            ("Volleys", "volley", sk.skill_by_zone(all_shots, net_zone, _phase_for_x, sport)),
        ]
        movement_label, movement_icon = "Movement", "movement"
    elif sport == "padel":
        net_zone = sk.NET_ZONE[sport]
        raw = [
            ("Serve", "serve", sk.skill_by_shot_index(points, 0)),
            ("Volley", "volley", sk.skill_by_zone(all_shots, net_zone, _phase_for_x, sport)),
            ("Défense", "defense", sk.skill_defense(all_shots, _phase_for_x, sport)),
            ("Lob", "lob", sk.skill_lob(all_shots, _phase_for_x, sport)),
            ("Smash", "smash", sk.skill_smash(all_shots, _phase_for_x, sport)),
        ]
        movement_label, movement_icon = "Positioning", "movement"
    else:
        net_zone = sk.NET_ZONE.get(sport, "Net")
        baseline_zone = sk.BASELINE_ZONE.get(sport, "Baseline")
        raw = [
            ("Serve", "serve", sk.skill_by_shot_index(points, 0)),
            ("Fond de court", "defense", sk.skill_by_zone(all_shots, baseline_zone, _phase_for_x, sport)),
            ("Régularité", "regularity", sk.skill_regularity(points)),
            ("Volley", "volley", sk.skill_by_zone(all_shots, net_zone, _phase_for_x, sport)),
            ("Return", "return", sk.skill_by_shot_index(points, 1)),
        ]
        movement_label, movement_icon = "Movement", "movement"

    skills = []
    for label, icon, quality in raw:
        if quality is None:
            continue
        score = sk.to_five_scale(quality)
        skills.append({"label": label, "icon": icon, "score": score, "color": _color_for_score(score)})

    skills.append({
        "label": movement_label, "icon": movement_icon,
        "score": movement_score, "color": _color_for_score(movement_score),
    })
    return skills


def _format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _build_highlights(points: list, detections: list, end_speeds: list, median_speed: float) -> list:
    highlights = []

    longest = max(points, key=len)
    highlights.append({
        "title": "Long échange", "time": _format_timestamp(longest[0].start_t),
        "tag": "Long échange", "tag_class": "tag-rally",
    })

    winner_idxs = [i for i, s in enumerate(end_speeds) if s >= median_speed]
    if winner_idxs:
        fastest_i = max(winner_idxs, key=lambda i: end_speeds[i])
        pt = points[fastest_i]
        highlights.append({
            "title": "Coup gagnant puissant", "time": _format_timestamp(pt[-1].end_t),
            "tag": "Winner", "tag_class": "tag-winner",
        })

    def spread(point):
        start_t, end_t = point[0].start_t, point[-1].end_t
        pts = [xy for f in detections if start_t <= f.t <= end_t for xy in f.player_xys]
        if len(pts) < 2:
            return 0.0
        arr = np.array(pts)
        return float(np.max(arr[:, 1]) - np.min(arr[:, 1]))

    attacking = max(points, key=spread, default=None)
    if attacking is not None and spread(attacking) > 0:
        highlights.append({
            "title": "Séquence offensive réussie", "time": _format_timestamp(attacking[0].start_t),
            "tag": "Attaque", "tag_class": "tag-attack",
        })

    error_idxs = [i for i, s in enumerate(end_speeds) if s < median_speed]
    if error_idxs:
        longest_defended_i = max(error_idxs, key=lambda i: len(points[i]))
        pt = points[longest_defended_i]
        if len(pt) > 1:
            highlights.append({
                "title": "Bonne défense", "time": _format_timestamp(pt[0].start_t),
                "tag": "Défense", "tag_class": "tag-defense",
            })

    return highlights[:4]


def _compute_patterns(events: list, sport: str) -> dict:
    import pandas as pd
    from backend.patterns_engine import compute_match_patterns

    if not events:
        df = pd.DataFrame(columns=["event_type", "phase", "x"])
    else:
        df = pd.DataFrame(events)
    return compute_match_patterns(df, sport=sport)