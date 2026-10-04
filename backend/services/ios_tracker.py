"""
Suivi d'objets image par image — port fidèle de ObjectTracker.swift (app iOS).

Objectif : que le web regroupe les détections en « pistes » exactement selon
les règles de l'application iOS, pour que les deux plateformes comptent les
échanges de la même façon (étapes suivantes : regroupement en échanges, puis
classement winner/erreur).

Règles reprises de l'iOS (valeurs par défaut de ObjectTracker) :
  - association par chevauchement (IoU) >= 0,3, parmi les détections de la même classe ;
  - pour la BALLE uniquement, repli sur la détection la plus proche si sa distance
    entre centres (coordonnées normalisées 0-1) est <= 0,4 ;
  - une détection non associée crée une nouvelle piste ;
  - une piste est terminée si elle n'a rien reçu depuis plus de 30 images
    ÉCHANTILLONNÉES, ou si sa confiance moyenne est < 0,3 ;
  - les images sans AUCUNE détection ne sont pas traitées (comme iOS, qui
    groupe les détections par numéro d'image) ;
  - l'ordre est : mise à jour des écarts, association, création, terminaison
    (l'association a donc lieu AVANT la terminaison, comme sur iOS).

Différence connue et volontaire : iOS parcourt ses pistes actives dans l'ordre
d'un dictionnaire Swift (non défini) ; ici l'ordre de création est utilisé, ce
qui rend le résultat déterministe.
"""
from dataclasses import dataclass, field

IOU_THRESHOLD = 0.3
MAX_FRAME_GAP = 30
MIN_CONFIDENCE = 0.3
BALL_MAX_MATCH_DISTANCE = 0.4


@dataclass
class Detection:
    frame: int            # index de l'image échantillonnée (0, 1, 2, ...)
    cls: str              # "ball" ou "player"
    box: tuple            # (x1, y1, x2, y2), coordonnées normalisées 0-1
    confidence: float
    t: float = 0.0        # instant en secondes dans la vidéo


@dataclass
class Track:
    cls: str
    detections: list = field(default_factory=list)

    @property
    def average_confidence(self) -> float:
        if not self.detections:
            return 0.0
        return sum(d.confidence for d in self.detections) / len(self.detections)

    @property
    def trajectory(self) -> list:
        """Centres successifs des détections (comme Track.trajectory sur iOS)."""
        return [((d.box[0] + d.box[2]) / 2, (d.box[1] + d.box[3]) / 2) for d in self.detections]

    @property
    def start_frame(self) -> int:
        return self.detections[0].frame

    @property
    def end_frame(self) -> int:
        return self.detections[-1].frame


def _iou(a: tuple, b: tuple) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = ix2 - ix1, iy2 - iy1
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def _centroid_distance(a: tuple, b: tuple) -> float:
    dx = (a[0] + a[2]) / 2 - (b[0] + b[2]) / 2
    dy = (a[1] + a[3]) / 2 - (b[1] + b[3]) / 2
    return (dx * dx + dy * dy) ** 0.5


class _State:
    def __init__(self, detection: Detection):
        self.track = Track(cls=detection.cls, detections=[detection])
        self.frame_gap = 0


def track_detections(detections: list) -> list:
    """Regroupe des détections en pistes (liste de Track). Liste vide si rien à suivre."""
    if not detections:
        return []

    by_frame = {}
    for det in detections:
        by_frame.setdefault(det.frame, []).append(det)

    active: list = []      # pistes actives, dans l'ordre de création
    completed: list = []

    for frame in sorted(by_frame):
        # 1. écart de chaque piste active depuis sa dernière détection
        for state in active:
            state.frame_gap = frame - state.track.detections[-1].frame

        # 2. association (chaque détection ne peut servir qu'une fois)
        unmatched = list(by_frame[frame])
        matched = []
        for state in active:
            last = state.track.detections[-1]
            best_iou = None       # (détection, iou)
            best_dist = None      # (détection, distance)
            for det in unmatched:
                if det.cls != state.track.cls:
                    continue
                iou = _iou(last.box, det.box)
                if iou >= IOU_THRESHOLD and (best_iou is None or iou > best_iou[1]):
                    best_iou = (det, iou)
                dist = _centroid_distance(last.box, det.box)
                if best_dist is None or dist < best_dist[1]:
                    best_dist = (det, dist)

            best = best_iou
            if best is None and state.track.cls == "ball" and best_dist is not None \
                    and best_dist[1] <= BALL_MAX_MATCH_DISTANCE:
                best = best_dist

            if best is not None:
                matched.append((state, best[0]))
                unmatched = [d for d in unmatched if d is not best[0]]

        # 3. mise à jour des pistes associées
        for state, det in matched:
            state.track.detections.append(det)
            state.frame_gap = 0

        # 4. nouvelle piste pour chaque détection non associée
        for det in unmatched:
            active.append(_State(det))

        # 5. terminaison (écart trop long ou confiance moyenne trop basse)
        still_active = []
        for state in active:
            if state.frame_gap > MAX_FRAME_GAP or state.track.average_confidence < MIN_CONFIDENCE:
                completed.append(state.track)
            else:
                still_active.append(state)
        active = still_active

    # 6. clôture des pistes restantes
    completed.extend(state.track for state in active)
    return completed


def ball_trajectories(tracks: list) -> list:
    """Pistes de balle exploitables : au moins 2 points (comme extractBallTrajectories sur iOS)."""
    return [t for t in tracks if t.cls == "ball" and len(t.detections) >= 2]