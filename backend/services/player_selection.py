"""
Préparation du choix du joueur : regroupe les détections de joueurs, puis produit
pour chaque candidat une vignette et des statistiques.

Cette étape est facultative : si elle échoue, l'analyse du match continue sans elle.
"""
import base64
import logging
from typing import Optional

import cv2

from backend.services.player_identification import PlayerDetection, identify_players
from backend.services.player_stats import compute_player_stats, scoped_view

logger = logging.getLogger("nextmove.player_selection")

THUMBNAIL_WIDTH = 160
JPEG_QUALITY = 70
BOX_MARGIN = 0.15  # marge autour de la boîte détectée, en fraction de sa taille


def make_thumbnail(video_path, t: float, box: tuple) -> Optional[str]:
    """Image du joueur à l'instant t (data URL JPEG), ou None si elle est illisible."""
    cap = cv2.VideoCapture(str(video_path))
    try:
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            return None
    finally:
        cap.release()

    height, width = frame.shape[:2]
    x1, y1, x2, y2 = box
    margin_x, margin_y = (x2 - x1) * BOX_MARGIN, (y2 - y1) * BOX_MARGIN
    left, right = max(0, int((x1 - margin_x) * width)), min(width, int((x2 + margin_x) * width))
    top, bottom = max(0, int((y1 - margin_y) * height)), min(height, int((y2 + margin_y) * height))
    if right - left < 2 or bottom - top < 2:
        return None

    crop = frame[top:bottom, left:right]
    new_height = max(1, int(crop.shape[0] * THUMBNAIL_WIDTH / crop.shape[1]))
    crop = cv2.resize(crop, (THUMBNAIL_WIDTH, new_height), interpolation=cv2.INTER_AREA)
    ok, buffer = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    if not ok:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buffer.tobytes()).decode("ascii")


def player_payload(candidate, thumbnail: Optional[str]) -> dict:
    """Ce qui est enregistré pour un joueur détecté (sérialisable en JSON)."""
    return {
        "index": candidate.index,
        "label": candidate.label,
        "side": candidate.side,
        "lane": candidate.lane,
        "is_likely_user": candidate.is_likely_user,
        "thumbnail": thumbnail,
        "stats": compute_player_stats(candidate),
    }


def build_player_payloads(video_path, track_inputs) -> list:
    """Joueurs détectés avec vignette et statistiques ; liste vide si l'étape échoue."""
    try:
        detections = [
            PlayerDetection(t=d.t, box=tuple(d.box), confidence=d.confidence)
            for d in track_inputs if d.cls == "player"
        ]
        return [
            player_payload(c, make_thumbnail(video_path, c.thumbnail_time, c.thumbnail_box))
            for c in identify_players(detections)
        ]
    except Exception:
        logger.exception("Identification des joueurs impossible : analyse poursuivie sans elle")
        return []



def scoped_fields(players, selected_index, rating, coverage, skills) -> dict:
    """Valeurs du match à afficher pour le joueur choisi ; {} si aucun joueur n'est choisi."""
    if selected_index is None:
        return {}
    for player in players or []:
        if player.get("index") == selected_index:
            return scoped_view(rating, coverage, skills, player.get("stats") or {})
    return {}



def viewed_fields(match) -> dict:
    """Note, couverture et compétences d'un match, vus pour le joueur choisi (ou tels quels)."""
    values = {"rating": match.rating, "coverage": match.coverage, "skills": match.skills}
    values.update(scoped_fields(match.players, match.selected_player_index,
                                match.rating, match.coverage, match.skills))
    return values