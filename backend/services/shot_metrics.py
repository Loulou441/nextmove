"""
Mesures par coup (vitesse, zone du terrain), calculées à partir d'un Shot
(rally_builder.py). Sert de base au calcul des compétences par coup
(Serve, Return, Third Shot, Dinking, Volleys...), à la place d'un simple
décalage arbitraire autour de la note globale.
"""


def shot_speed(shot) -> float:
    """
    Vitesse moyenne du coup : distance parcourue par la balle sur sa
    trajectoire, divisée par sa durée. En unités de cadre par seconde
    (même échelle que Track.trajectory : 0-1 sur chaque axe).
    Renvoie 0.0 si la trajectoire est trop courte ou instantanée.
    """
    points = shot.trajectory.trajectory
    if len(points) < 2:
        return 0.0
    duration = shot.end_t - shot.start_t
    if duration <= 0:
        return 0.0
    (x0, y0), (x1, y1) = points[0], points[-1]
    distance = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return distance / duration


def shot_zone(shot, phase_for_x, sport: str) -> str:
    """
    Zone du terrain où se termine le coup, via la fonction phase_for_x déjà
    utilisée par le reste du pipeline (_phase_for_x dans cv_pipeline.py),
    pour rester cohérent avec le reste de l'analyse (répartition par zone).
    La position de fin de trajectoire est convertie sur l'échelle 0-100
    attendue par phase_for_x (trajectoire en 0-1).
    """
    x_end = shot.trajectory.trajectory[-1][0] * 100
    return phase_for_x(x_end, sport)