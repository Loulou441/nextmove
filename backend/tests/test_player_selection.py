import base64
from collections import namedtuple
from types import SimpleNamespace
import cv2
import numpy as np
import pytest

from backend.services.player_selection import build_player_payloads, make_thumbnail, scoped_fields, viewed_fields

Input = namedtuple("Input", "cls t box confidence")
BOX = (100 / 320, 60 / 240, 140 / 320, 140 / 240)  # rectangle blanc de la vidéo de test


@pytest.fixture
def video(tmp_path):
    path = tmp_path / "test.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (320, 240))
    for _ in range(20):
        frame = np.full((240, 320, 3), 40, dtype=np.uint8)
        cv2.rectangle(frame, (100, 60), (140, 140), (255, 255, 255), -1)
        writer.write(frame)
    writer.release()
    return path


def _decode(data_url):
    raw = base64.b64decode(data_url.split(",", 1)[1])
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)


def test_vignette_recadree_sur_le_joueur(video):
    url = make_thumbnail(video, 0.5, BOX)
    assert url.startswith("data:image/jpeg;base64,")
    image = _decode(url)
    assert image.shape[1] == 160
    h, w = image.shape[:2]
    assert image[h // 2 - 5:h // 2 + 5, w // 2 - 5:w // 2 + 5].mean() > 200  # centre = joueur blanc


def test_vignette_video_illisible(tmp_path):
    assert make_thumbnail(tmp_path / "absente.avi", 0.0, BOX) is None


def test_vignette_boite_degeneree(video):
    assert make_thumbnail(video, 0.5, (0.5, 0.5, 0.5, 0.5)) is None


def _joueurs(cx, cy, n=20):
    # petites variations de position, comme un vrai joueur (jamais strictement immobile)
    return [
        Input("player", i * 0.05, (cx - 0.04 + 0.01 * ((i % 5) - 2), cy - 0.1 + 0.01 * ((i % 3) - 1),
                                   cx + 0.04 + 0.01 * ((i % 5) - 2), cy + 0.1 + 0.01 * ((i % 3) - 1)), 0.9)
        for i in range(n)
    ]


def test_payloads_deux_joueurs_avec_vignette_et_stats(video):
    payloads = build_player_payloads(video, _joueurs(0.5, 0.8) + _joueurs(0.5, 0.25))
    assert [p["label"] for p in payloads] == ["Premier plan", "Arrière-plan"]
    assert payloads[0]["is_likely_user"] and payloads[0]["thumbnail"].startswith("data:image/jpeg")
    assert {"coverage_percent", "zones", "left_right_balance"} <= set(payloads[0]["stats"])


def test_payloads_ignorent_la_balle(video):
    balle = [Input("ball", i * 0.05, (0.4, 0.4, 0.42, 0.42), 0.8) for i in range(20)]
    assert build_player_payloads(video, balle) == []


def test_payloads_ne_font_jamais_echouer_l_analyse(video):
    assert build_player_payloads(video, [object()]) == []




PLAYERS = [{"index": 1, "stats": {"coverage_percent": 10.0}}, {"index": 2, "stats": {"coverage_percent": 25.0}}]
SKILLS = [
    {"label": "Serve", "icon": "serve", "score": 3.2, "color": "blue"},
    {"label": "Movement", "icon": "movement", "score": 5.0, "color": "green"},
]


def test_vue_sans_joueur_choisi():
    assert scoped_fields(PLAYERS, None, 4.2, 70, SKILLS) == {}


def test_vue_joueur_inconnu():
    assert scoped_fields(PLAYERS, 9, 4.2, 70, SKILLS) == {}


def test_vue_sans_joueurs_detectes():
    assert scoped_fields(None, 1, 4.2, 70, SKILLS) == {}


def test_vue_joueur_choisi():
    vue = scoped_fields(PLAYERS, 1, 4.2, 70, SKILLS)
    assert vue["coverage"] == 10 and vue["rating"] == 3.7
    assert vue["skills"][1]["score"] == 3.8




def _match(selected):
    return SimpleNamespace(rating=4.2, coverage=70, skills=SKILLS, players=PLAYERS, selected_player_index=selected)


def test_valeurs_affichees_sans_joueur_choisi():
    assert viewed_fields(_match(None)) == {"rating": 4.2, "coverage": 70, "skills": SKILLS}


def test_valeurs_affichees_pour_le_joueur_choisi():
    valeurs = viewed_fields(_match(1))
    assert valeurs["rating"] == 3.7 and valeurs["coverage"] == 10