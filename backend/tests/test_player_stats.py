from backend.services.player_identification import PlayerCandidate
from backend.services.player_stats import compute_player_stats, scoped_view


def cand(positions, conf=0.9):
    return PlayerCandidate(index=1, side="near", lane=None, positions=positions,
                           average_position=(0.5, 0.5), average_confidence=conf,
                           thumbnail_time=0.0, thumbnail_box=(0, 0, 1, 1), is_likely_user=True)


def test_stats_sans_position():
    s = compute_player_stats(cand([]))
    assert s["detection_count"] == 0 and s["coverage_percent"] == 0.0
    assert len(s["zones"]) == 9


def test_couverture_par_enveloppe_convexe():
    carre = [(0.2, 0.2), (0.6, 0.2), (0.6, 0.6), (0.2, 0.6), (0.4, 0.4), (0.3, 0.5)]
    assert compute_player_stats(cand(carre))["coverage_percent"] == 16.0


def test_points_alignes_sans_surface():
    assert compute_player_stats(cand([(0.1, 0.5), (0.5, 0.5), (0.9, 0.5)]))["coverage_percent"] == 0.0


def test_zones_profondeur_et_equilibre_a_droite():
    s = compute_player_stats(cand([(0.9, 0.9)] * 5))
    assert s["zones"]["front_right"] == 1.0
    assert abs(sum(s["zones"].values()) - 1.0) < 1e-9
    assert s["left_right_balance"] == 1.0 and s["average_depth"] == 0.9


def test_equilibre_a_gauche():
    assert compute_player_stats(cand([(0.1, 0.5)] * 4))["left_right_balance"] == -1.0


def test_vue_joueur_remplace_le_deplacement_et_la_note():
    skills = [
        {"label": "Serve", "icon": "serve", "score": 3.2, "color": "blue"},
        {"label": "Movement", "icon": "movement", "score": 5.0, "color": "green"},
    ]
    vue = scoped_view(4.2, 70, skills, {"coverage_percent": 10.0})
    assert vue["skills"][0] == skills[0]
    assert vue["skills"][1]["score"] == 3.8 and vue["skills"][1]["color"] == "blue"
    assert vue["rating"] == 3.7 and vue["coverage"] == 10
    assert skills[1]["score"] == 5.0  # le match d'origine n'est pas modifié


def test_vue_sans_competence_de_deplacement():
    skills = [{"label": "Serve", "icon": "serve", "score": 3.2, "color": "blue"}]
    assert scoped_view(4.0, 40, skills, {"coverage_percent": 20.0})["skills"] == skills


def test_note_reste_dans_ses_bornes():
    assert scoped_view(5.0, 0, [], {"coverage_percent": 100.0})["rating"] == 5.0
    assert scoped_view(3.0, 70, [], {"coverage_percent": 0.0})["rating"] == 3.0