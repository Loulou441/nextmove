"""
Identification des joueurs par sélection.

Regroupe les détections de joueurs d'une analyse en 2 à 4 « candidats »
stables, pour que l'utilisateur désigne celui qui est lui. Le regroupement
repose uniquement sur la position : les joueurs gardent leur côté du filet
(séparés en profondeur), puis, en double, se répartissent à gauche et à droite.

Les objets fixes (tableau d'affichage, logo, spectateur) sont écartés : un joueur ne reste
jamais parfaitement immobile pendant tout le clip.

Une coupure (profondeur ou gauche/droite) n'est retenue que si les deux groupes
sont vus ensemble dans les mêmes images : un joueur seul qui se déplace ne peut pas
se trouver à deux endroits à la fois, il n'est donc jamais dupliqué.

Portée assumée : identification par sélection, pas de ré-identification
visuelle. Un joueur qui quitte longtemps le champ peut être fusionné avec un
autre groupe. Caméra fixe supposée.
"""
from dataclasses import dataclass
from typing import Optional

MIN_DETECTIONS = 3
MAX_CANDIDATES = 4
MIN_RELATIVE_SUPPORT = 0.35
BACKGROUND_AREA_FRACTION = 0.30
MIN_CO_OCCURRENCE = 0.25   # deux joueurs distincts sont vus ensemble dans les mêmes images
STATIONARY_TOLERANCE = 0.006   # position (fraction de l'image) en deçà de laquelle un objet est « au même endroit »
STATIONARY_SIZE_TOLERANCE = 0.10
STATIONARY_MIN_SHARE = 0.20    # part des images où l'objet fixe est présent
STATIONARY_MIN_SPAN = 0.60     # part de la durée du clip qu'il couvre
_LANE_BINS = 10


@dataclass(frozen=True)
class PlayerDetection:
    """Une détection de joueur : instant (s), boîte normalisée (x1, y1, x2, y2), confiance."""
    t: float
    box: tuple
    confidence: float

    @property
    def mid_x(self) -> float:
        return (self.box[0] + self.box[2]) / 2

    @property
    def mid_y(self) -> float:
        return (self.box[1] + self.box[3]) / 2

    @property
    def area(self) -> float:
        return max(0.0, self.box[2] - self.box[0]) * max(0.0, self.box[3] - self.box[1])


@dataclass
class PlayerCandidate:
    index: int                  # 1 à 4, le premier plan à gauche d'abord
    side: str                   # "near" (premier plan) ou "far" (arrière-plan)
    lane: Optional[str]         # "left", "right" ou None
    positions: list             # [(x, y)] normalisés, dans l'ordre du temps
    average_position: tuple
    average_confidence: float
    thumbnail_time: float
    thumbnail_box: tuple
    is_likely_user: bool

    @property
    def label(self) -> str:
        base = "Premier plan" if self.side == "near" else "Arrière-plan"
        if self.lane is None:
            return base
        return f"{base}, {'gauche' if self.lane == 'left' else 'droite'}"


def identify_players(detections: list) -> list:
    """Construit les candidats, premier plan d'abord ; liste vide si aucun joueur."""
    players = list(detections)
    if not players:
        return []

    # 0. Écarte les « joueurs » qui ne bougent jamais (tableau d'affichage, logo, spectateur).
    players = _drop_stationary(players)
    if not players:
        return []

    # 1. Sépare en profondeur, là où les joueurs sont naturellement séparés, et
    #    seulement si les deux côtés sont vus ensemble.
    split_y = _depth_threshold(players)
    near_half = [d for d in players if d.mid_y >= split_y]
    far_half = [d for d in players if d.mid_y < split_y]
    if near_half and far_half and _co_occurrence(near_half, far_half) >= MIN_CO_OCCURRENCE:
        depth_groups = [near_half, far_half]
    else:
        depth_groups = [players]

    # 2. À profondeur comparable, écarte les boîtes bien plus petites (terrain voisin),
    #    puis cherche un joueur (simple) ou deux (double) dans chaque groupe.
    clusters = [c for group in depth_groups for c in _split_half(_drop_small(group))]

    # 3. Écarte le bruit, garde les groupes les mieux soutenus, plafonne à 4.
    kept = [c for c in clusters if len(c) >= MIN_DETECTIONS] or clusters
    kept.sort(key=len, reverse=True)
    floor = max(MIN_DETECTIONS, int(len(kept[0]) * MIN_RELATIVE_SUPPORT))
    kept = [c for c in kept if len(c) >= floor][:MAX_CANDIDATES]

    # 4. Un candidat par groupe.
    provisional = []
    for cluster in kept:
        in_time = sorted(cluster, key=lambda d: d.t)
        provisional.append({
            "avg": (sum(d.mid_x for d in cluster) / len(cluster),
                    sum(d.mid_y for d in cluster) / len(cluster)),
            "conf": sum(d.confidence for d in cluster) / len(cluster),
            "best": max(cluster, key=lambda d: d.area * d.confidence),
            "positions": [(d.mid_x, d.mid_y) for d in in_time],
        })

    ys = sorted(p["avg"][1] for p in provisional)
    pivot_y = 0.5 if len(provisional) == 1 else ys[len(provisional) // 2]

    def is_near(p) -> bool:
        return p["avg"][1] >= pivot_y

    provisional.sort(key=lambda p: (not is_near(p), p["avg"][0]))
    near_count = sum(1 for p in provisional if is_near(p))
    far_count = len(provisional) - near_count

    result = []
    for i, p in enumerate(provisional):
        near = is_near(p)
        on_side = near_count if near else far_count
        lane = None
        if on_side >= 2:
            lane = "left" if p["avg"][0] < 0.5 else "right"
        result.append(PlayerCandidate(
            index=i + 1,
            side="near" if near else "far",
            lane=lane,
            positions=p["positions"],
            average_position=p["avg"],
            average_confidence=p["conf"],
            thumbnail_time=p["best"].t,
            thumbnail_box=p["best"].box,
            is_likely_user=(i == 0),
        ))
    return result


def _drop_stationary(players: list) -> list:
    """Écarte les détections d'objets fixes : même endroit, même taille, sur tout le clip.

    Un joueur qui attend le service reste immobile quelques secondes seulement ; un
    objet fixe est détecté au même endroit pendant une part notable du clip entier.
    """
    frames = {round(d.t, 3) for d in players}
    duration = max(d.t for d in players) - min(d.t for d in players)
    if len(frames) < 2 or duration <= 0:
        return players

    def is_stationary(d) -> bool:
        same = [
            e for e in players
            if abs(e.mid_x - d.mid_x) <= STATIONARY_TOLERANCE
            and abs(e.mid_y - d.mid_y) <= STATIONARY_TOLERANCE
            and abs(e.area - d.area) <= STATIONARY_SIZE_TOLERANCE * d.area
        ]
        seen = {round(e.t, 3) for e in same}
        span = max(e.t for e in same) - min(e.t for e in same)
        return (len(seen) >= STATIONARY_MIN_SHARE * len(frames)
                and span >= STATIONARY_MIN_SPAN * duration)

    return [d for d in players if not is_stationary(d)]


def _drop_small(group: list) -> list:
    """À profondeur comparable, écarte les boîtes bien plus petites : joueurs d'un terrain voisin."""
    areas = sorted(d.area for d in group)
    min_area = areas[len(areas) // 2] * BACKGROUND_AREA_FRACTION
    filtered = [d for d in group if d.area >= min_area]
    if len(filtered) >= max(MIN_DETECTIONS, len(group) // 3):
        return filtered
    return group


def _split_half(half: list) -> list:
    """Sépare une moitié du terrain en un ou deux joueurs selon un vide latéral net."""
    if len(half) < MIN_DETECTIONS:
        return [half] if half else []

    counts = [0] * _LANE_BINS
    for d in half:
        counts[min(_LANE_BINS - 1, max(0, int(d.mid_x * _LANE_BINS)))] += 1

    noise_floor = max(1, len(half) // (_LANE_BINS * 2))
    populated = [i for i, c in enumerate(counts) if c > noise_floor]
    if len(populated) < 2:
        return [half]
    first_pop, last_pop = populated[0], populated[-1]

    best_start, best_len, run_start, run_len = -1, 0, -1, 0
    for b in range(first_pop + 1, last_pop):
        if counts[b] <= noise_floor:
            if run_start < 0:
                run_start, run_len = b, 0
            run_len += 1
            if run_len > best_len:
                best_len, best_start = run_len, run_start
        else:
            run_start, run_len = -1, 0

    if best_len < 2 or best_start <= 0:
        return [half]

    split_x = (best_start + best_len / 2) / _LANE_BINS
    left = [d for d in half if d.mid_x < split_x]
    right = [d for d in half if d.mid_x >= split_x]
    if len(left) < MIN_DETECTIONS or len(right) < MIN_DETECTIONS:
        return [half]
    if _co_occurrence(left, right) < MIN_CO_OCCURRENCE:
        return [half]  # jamais vus ensemble : un seul joueur qui a changé de côté
    return [left, right]


def _co_occurrence(a: list, b: list) -> float:
    """Part des instants du plus petit groupe où l'autre groupe est aussi présent."""
    times_a = {round(d.t, 3) for d in a}
    times_b = {round(d.t, 3) for d in b}
    smaller = min(len(times_a), len(times_b))
    return len(times_a & times_b) / smaller if smaller else 0.0


def _depth_threshold(players: list) -> float:
    """Seuil de profondeur qui sépare au mieux deux groupes (variance inter-classes maximale)."""
    ys = sorted(d.mid_y for d in players)
    n = len(ys)
    total = sum(ys)
    best_score, best_threshold = -1.0, ys[n // 2]
    cumulative = 0.0
    for i in range(1, n):
        cumulative += ys[i - 1]
        if ys[i] == ys[i - 1]:
            continue
        mean_low = cumulative / i
        mean_high = (total - cumulative) / (n - i)
        score = (i / n) * ((n - i) / n) * (mean_high - mean_low) ** 2
        if score > best_score:
            best_score, best_threshold = score, (ys[i - 1] + ys[i]) / 2
    return best_threshold