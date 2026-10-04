"""
Regroupement des trajectoires de balle en points, puis des points en coups
individuels classés (1er, 2e, 3e...), pour permettre un calcul de compétences
par coup plutôt que par point entier.

Repose sur ios_tracker.track_detections / ball_trajectories, qui reconstruit
déjà les trajectoires de balle à partir des détections brutes.

Règle de regroupement en points, en deux temps :
  1. Écart de temps : deux trajectoires trop éloignées dans le temps ne
     peuvent pas appartenir au même point (comme sur iOS).
  2. Alternance de sens : à l'intérieur de cette fenêtre de temps, deux
     coups qui vont dans le MÊME sens (tous deux vers le filet, ou tous deux
     vers le fond) ne sont probablement pas un vrai échange qui se poursuit
     — par exemple une balle qui continue de rouler après la fin du point.
     Un vrai échange alterne : un coup rapproche la balle du filet, le
     suivant l'en éloigne. Seule une alternance de sens confirme la
     continuité du même point ; un coup "plat" (déplacement trop faible
     pour trancher) est accepté par défaut, faute de signal contraire.
"""
from dataclasses import dataclass

MAX_GAP_SECONDS = 3.0

# Variation de position (sur l'axe 0-1 du suivi) en dessous de laquelle un
# coup est considéré "plat" : ni clairement vers le filet, ni clairement
# vers le fond. Évite de trancher sur du bruit de détection.
FLAT_THRESHOLD = 0.05


@dataclass
class Shot:
    """Un coup : une trajectoire de balle, avec sa position dans le point."""
    trajectory: object   # Track (voir ios_tracker.py)
    index_in_point: int  # 0 = premier coup du point, 1 = deuxième, ...
    start_t: float
    end_t: float
    trend: str            # "forward" (vers le filet), "backward" (vers le fond), "flat"


def _trajectory_times(trajectory, frame_to_time) -> tuple:
    return frame_to_time(trajectory.start_frame), frame_to_time(trajectory.end_frame)


def _trend(trajectory) -> str:
    """Sens de déplacement de la balle sur l'axe x de sa trajectoire (0-1)."""
    points = trajectory.trajectory
    if len(points) < 2:
        return "flat"
    dx = points[-1][0] - points[0][0]
    if abs(dx) < FLAT_THRESHOLD:
        return "flat"
    return "forward" if dx > 0 else "backward"


def _same_point(previous_trend: str, current_trend: str) -> bool:
    """
    Deux coups appartiennent au même point sauf si leurs sens sont tous les
    deux connus ET identiques (pas d'alternance = pas d'échange réel).
    """
    if previous_trend == "flat" or current_trend == "flat":
        return True  # signal insuffisant pour trancher : on ne coupe pas à tort
    return previous_trend != current_trend


def build_points(ball_trajectories: list, frame_to_time) -> list:
    """
    Regroupe des trajectoires de balle (triées ou non) en points.
    `frame_to_time` convertit un index d'image échantillonnée en secondes.
    Renvoie une liste de points, chaque point étant une liste de Shot,
    triés par ordre chronologique à l'intérieur du point.
    """
    if not ball_trajectories:
        return []

    ordered = sorted(ball_trajectories, key=lambda tr: tr.start_frame)

    points: list = []
    current: list = []
    last_end_t = None
    last_trend = None

    for traj in ordered:
        start_t, end_t = _trajectory_times(traj, frame_to_time)
        trend = _trend(traj)

        too_far_in_time = last_end_t is not None and (start_t - last_end_t) > MAX_GAP_SECONDS
        same_direction_twice = last_trend is not None and not _same_point(last_trend, trend)

        if too_far_in_time or same_direction_twice:
            points.append(current)
            current = []

        current.append(Shot(
            trajectory=traj, index_in_point=len(current),
            start_t=start_t, end_t=end_t, trend=trend,
        ))
        last_end_t = end_t
        last_trend = trend

    if current:
        points.append(current)

    return points