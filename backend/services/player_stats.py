"""
Statistiques par joueur et vue du match pour un joueur choisi.

Seules les mesures issues des positions propres au joueur sont recalculées :
couverture, répartition par zone, équilibre gauche/droite, profondeur moyenne,
compétence de déplacement et note globale. Les mesures liées à la balle
(échanges, winners, service, volley...) appartiennent au match : elles restent
inchangées et se présentent comme contexte du match.
"""
PLAYER_COVERAGE_REFERENCE = 25.0   # % de l'image couvert par un joueur très mobile
MATCH_COVERAGE_REFERENCE = 70.0    # référence du calcul de match (tous les joueurs)
_ROWS = ("back", "mid", "front")
_COLS = ("left", "center", "right")


def color_for_score(score: float) -> str:
    """Mêmes seuils que les compétences du pipeline (cv_pipeline._color_for_score)."""
    if score >= 4.0:
        return "green"
    if score >= 3.0:
        return "blue"
    return "orange"


def compute_player_stats(candidate) -> dict:
    """Résumé mesuré d'un joueur, sérialisable en JSON."""
    points = candidate.positions
    zones = {f"{r}_{c}": 0.0 for r in _ROWS for c in _COLS}
    if not points:
        return {"coverage_percent": 0.0, "zones": zones, "left_right_balance": 0.0,
                "average_depth": 0.0, "detection_count": 0, "average_confidence": 0.0}

    counts = {key: 0 for key in zones}
    left = right = 0
    depth_sum = 0.0
    for x, y in points:
        col = 0 if x < 0.33 else (1 if x < 0.67 else 2)
        row = 0 if y < 0.33 else (1 if y < 0.67 else 2)
        counts[f"{_ROWS[row]}_{_COLS[col]}"] += 1
        if x < 0.5:
            left += 1
        else:
            right += 1
        depth_sum += y

    total = len(points)
    return {
        "coverage_percent": round(_hull_area_percent(points), 1),
        "zones": {key: round(n / total, 3) for key, n in counts.items()},
        "left_right_balance": round((right - left) / total, 3),
        "average_depth": round(depth_sum / total, 3),
        "detection_count": total,
        "average_confidence": round(float(candidate.average_confidence), 3),
    }


def scoped_view(rating, coverage, skills, stats: dict) -> dict:
    """Note, couverture et compétences du match, avec le déplacement du joueur choisi.

    Le déplacement et la note sont recalculés avec la couverture du joueur seul
    (référence de 25 % de l'image, contre 70 % pour l'ensemble des joueurs). Le
    reste de la note, issu de la balle, est déduit de la note du match.
    """
    player_cov = float(stats.get("coverage_percent", 0.0))
    norm_player = min(player_cov / PLAYER_COVERAGE_REFERENCE, 1.0)

    new_skills = []
    for skill in skills or []:
        if skill.get("icon") == "movement":
            score = round(3.0 + 2.0 * norm_player, 1)
            skill = {**skill, "score": score, "color": color_for_score(score)}
        new_skills.append(skill)

    new_rating = rating
    if rating is not None and coverage is not None:
        norm_match = min(coverage / MATCH_COVERAGE_REFERENCE, 1.0)
        rest = (rating - 3.0) / 2.0 - 0.45 * norm_match
        rest = max(0.0, min(0.55, rest))
        new_rating = round(3.0 + 2.0 * (0.45 * norm_player + rest), 1)

    return {"rating": new_rating, "coverage": int(round(player_cov)), "skills": new_skills}


def _hull_area_percent(points: list) -> float:
    """Aire de l'enveloppe convexe en % de l'image (coordonnées normalisées)."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return 0.0

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return 0.0
    n = len(hull)
    area = abs(sum(hull[i][0] * hull[(i + 1) % n][1] - hull[(i + 1) % n][0] * hull[i][1]
                   for i in range(n))) / 2.0
    return min(100.0, area * 100.0)