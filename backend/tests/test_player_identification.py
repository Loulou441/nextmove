import json
import random
from pathlib import Path

from backend.services.player_identification import PlayerDetection, identify_players


def det(t, cx, cy, w=0.08, h=0.2, conf=0.9):
    return PlayerDetection(t=t, box=(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), confidence=conf)


def group(cx, cy, n=20, spread=0.03, **kw):
    rnd = random.Random(int(cx * 100 + cy * 1000))
    return [det(i * 0.2, cx + rnd.uniform(-spread, spread), cy + rnd.uniform(-spread, spread), **kw)
            for i in range(n)]


def test_aucune_detection():
    assert identify_players([]) == []


def test_simple_deux_joueurs():
    res = identify_players(group(0.5, 0.8) + group(0.5, 0.25))
    assert len(res) == 2
    assert res[0].side == "near" and res[0].is_likely_user and res[0].lane is None
    assert res[1].side == "far" and not res[1].is_likely_user
    assert [c.label for c in res] == ["Premier plan", "Arrière-plan"]


def test_double_quatre_joueurs():
    dets = group(0.25, 0.8) + group(0.75, 0.8) + group(0.25, 0.25) + group(0.75, 0.25)
    res = identify_players(dets)
    assert [c.label for c in res] == [
        "Premier plan, gauche", "Premier plan, droite",
        "Arrière-plan, gauche", "Arrière-plan, droite",
    ]
    assert [c.index for c in res] == [1, 2, 3, 4]


def test_joueur_qui_se_deplace_reste_un_seul():
    mobile = [det(i * 0.2, 0.1 + 0.8 * i / 29, 0.8) for i in range(30)]
    res = identify_players(mobile + group(0.5, 0.25))
    assert len(res) == 2
    assert all(c.lane is None for c in res)


def test_joueur_d_un_terrain_voisin_ecarte():
    voisin = group(0.9, 0.1, n=15, w=0.02, h=0.05)
    res = identify_players(group(0.5, 0.8) + group(0.5, 0.25) + voisin)
    assert len(res) == 2


def test_miniature_sur_la_meilleure_detection():
    meilleure = det(99.0, 0.5, 0.8, w=0.12, h=0.3, conf=0.99)
    res = identify_players(group(0.5, 0.8) + [meilleure] + group(0.5, 0.25))
    assert res[0].thumbnail_time == 99.0
    assert res[0].thumbnail_box == meilleure.box


def test_positions_dans_l_ordre_du_temps():
    dets = group(0.5, 0.8) + group(0.5, 0.25)
    melange = dets[:]
    random.Random(1).shuffle(melange)
    assert identify_players(dets)[0].positions == identify_players(melange)[0].positions



def test_un_seul_joueur_qui_avance_vers_le_filet_n_est_pas_duplique():
    # un joueur seul, vu de plus en plus haut dans l'image : un seul candidat
    avance = [det(i * 0.2, 0.5, 0.9 - 0.3 * i / 39) for i in range(40)]
    assert len(identify_players(avance)) == 1


def test_un_seul_joueur_qui_change_de_cote_n_est_pas_duplique():
    # à gauche puis à droite, jamais les deux en même temps : un seul candidat
    cote = [det(i * 0.2, 0.2 if i < 20 else 0.8, 0.8) for i in range(40)]
    assert len(identify_players(cote)) == 1


def test_joueur_proche_dominant_et_joueur_lointain_restent_distincts():
    proche = [det(i * 0.2, 0.5 + 0.01 * ((i % 7) - 3), 0.8 + 0.1 * ((i % 5) - 2) / 2) for i in range(40)]
    lointain = [det(i * 0.2, 0.5, 0.3) for i in range(16)]  # vu pendant 16 des 40 instants
    res = identify_players(proche + lointain)
    assert [c.label for c in res] == ["Premier plan", "Arrière-plan"]
    assert len(res[0].positions) == 40



def test_objet_fixe_n_est_pas_un_joueur():
    # une boîte identique en haut de l'image pendant tout le clip (tableau d'affichage, logo...)
    fixe = [det(i * 0.2, 0.85, 0.15, w=0.3, h=0.3) for i in range(20)]
    res = identify_players(group(0.5, 0.8) + group(0.5, 0.3) + fixe)
    assert len(res) == 2
    assert all(c.average_position[1] > 0.25 for c in res)


def test_joueur_qui_attend_le_service_n_est_pas_ecarte():
    # immobile pendant un quart du clip seulement, puis en mouvement : toujours un joueur
    attente = [det(i * 0.2, 0.5, 0.8) for i in range(10)]
    mouvement = [det(i * 0.2, 0.5 + 0.02 * ((i % 7) - 3), 0.8 - 0.004 * (i - 10)) for i in range(10, 40)]
    res = identify_players(attente + mouvement + group(0.5, 0.3))
    assert [c.label for c in res] == ["Premier plan", "Arrière-plan"]
    assert len(res[0].positions) == 40


def test_video_reelle_tennis_amateur_deux_joueurs_sans_objet_fixe():
    # 88 détections réelles : un joueur proche, un joueur lointain, un objet fixe en haut à droite
    fichier = Path(__file__).parent / "fixtures" / "players_tennis_amateur.json"
    lignes = json.loads(fichier.read_text(encoding="utf-8"))
    res = identify_players([PlayerDetection(t=l["t"], box=tuple(l["box"]), confidence=l["confidence"]) for l in lignes])
    assert [c.label for c in res] == ["Premier plan", "Arrière-plan"]
    assert len(res[0].positions) >= 15 and len(res[1].positions) >= 15
    assert all(c.average_position[1] > 0.3 for c in res)