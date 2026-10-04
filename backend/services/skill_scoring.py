"""
Calcul des compétences par sport, à partir des coups réellement mesurés
(rally_builder.Shot), plutôt que d'un décalage arbitraire autour de la note
globale.

Principe général : chaque compétence est la qualité moyenne des coups qui
correspondent à son critère (position dans le point, zone du terrain,
vitesse). Une compétence sans coup correspondant sur ce match n'est pas
affichée avec une valeur inventée : elle est simplement absente.

Les seuils de vitesse (lent / rapide) sont des choix arbitraires raisonnables,
non calibrés sur des données réelles — à ajuster une fois validés sur le
terrain.
"""
from backend.services.shot_metrics import shot_speed, shot_zone

REFERENCE_SPEED = 1.0
SLOW_SPEED_THRESHOLD = 0.4
FAST_SPEED_THRESHOLD = 1.5

NET_ZONE = {"padel": "Net", "tennis": "Net", "pickleball": "Kitchen"}
BASELINE_ZONE = {"padel": "Baseline", "tennis": "Baseline", "pickleball": "Service"}


def shot_confidence(shot) -> float:
    """Confiance moyenne de détection sur les images de ce coup."""
    dets = shot.trajectory.detections
    if not dets:
        return 0.0
    return sum(d.confidence for d in dets) / len(dets)


def shot_quality(shot) -> float:
    """
    Qualité générique d'un coup, entre 0 et 1 : combine la confiance de
    détection (70 %) et une vitesse jugée contrôlée (30 %), plafonnée à la
    vitesse de référence pour ne pas favoriser une vitesse déraisonnable.
    """
    speed = shot_speed(shot)
    speed_score = min(speed / REFERENCE_SPEED, 1.0)
    return 0.7 * shot_confidence(shot) + 0.3 * speed_score


def _average_quality(shots: list) -> float | None:
    if not shots:
        return None
    return sum(shot_quality(s) for s in shots) / len(shots)


def skill_by_shot_index(points: list, index: int) -> float | None:
    """Qualité moyenne du coup situé à `index` (0 = premier) dans chaque point."""
    shots = [pt[index] for pt in points if len(pt) > index]
    return _average_quality(shots)


def skill_by_zone(all_shots: list, zone_label: str, phase_for_x, sport: str) -> float | None:
    """Qualité moyenne des coups qui se terminent dans une zone donnée."""
    shots = [s for s in all_shots if shot_zone(s, phase_for_x, sport) == zone_label]
    return _average_quality(shots)


def skill_dinking(all_shots: list, phase_for_x, sport: str) -> float | None:
    """Qualité des coups lents ET près du filet (jeu de dink au pickleball)."""
    zone = NET_ZONE.get(sport, "Net")
    shots = [
        s for s in all_shots
        if shot_zone(s, phase_for_x, sport) == zone and shot_speed(s) <= SLOW_SPEED_THRESHOLD
    ]
    return _average_quality(shots)


def skill_smash(all_shots: list, phase_for_x, sport: str) -> float | None:
    """Qualité des coups rapides ET près du filet (smash au padel)."""
    zone = NET_ZONE.get(sport, "Net")
    shots = [
        s for s in all_shots
        if shot_zone(s, phase_for_x, sport) == zone and shot_speed(s) >= FAST_SPEED_THRESHOLD
    ]
    return _average_quality(shots)


def skill_lob(all_shots: list, phase_for_x, sport: str) -> float | None:
    """Qualité des coups lents joués loin du filet (lob au padel)."""
    net_zone = NET_ZONE.get(sport, "Net")
    shots = [
        s for s in all_shots
        if shot_zone(s, phase_for_x, sport) != net_zone and shot_speed(s) <= SLOW_SPEED_THRESHOLD
    ]
    return _average_quality(shots)


def skill_defense(all_shots: list, phase_for_x, sport: str) -> float | None:
    """Qualité des coups en fond de court, hors le tout premier coup du point (le service)."""
    zone = BASELINE_ZONE.get(sport, "Baseline")
    shots = [
        s for s in all_shots
        if shot_zone(s, phase_for_x, sport) == zone and s.index_in_point > 0
    ]
    return _average_quality(shots)


def skill_regularity(points: list) -> float | None:
    """
    Constance de la vitesse entre coups consécutifs d'un même point : moins
    l'écart de vitesse d'un coup à l'autre est grand, plus le score est
    élevé. Renvoie None si aucun point n'a au moins 2 coups.
    """
    diffs = []
    for pt in points:
        speeds = [shot_speed(s) for s in pt]
        for a, b in zip(speeds, speeds[1:]):
            diffs.append(abs(a - b))
    if not diffs:
        return None
    avg_diff = sum(diffs) / len(diffs)
    return max(0.0, 1.0 - min(avg_diff / REFERENCE_SPEED, 1.0))


def to_five_scale(quality: float) -> float:
    """Convertit une qualité 0-1 en note 1-5, affichée à l'écran."""
    return round(1.0 + 4.0 * max(0.0, min(quality, 1.0)), 1)