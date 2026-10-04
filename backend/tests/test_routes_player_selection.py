"""Tests des routes de choix du joueur : GET /matches/{id} et PUT /matches/{id}/player."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch
from backend.db.models import Match
from backend.tests.conftest import make_fake_db, override_db

SKILLS = [
    {"label": "Serve", "icon": "serve", "score": 3.2, "color": "blue"},
    {"label": "Movement", "icon": "movement", "score": 5.0, "color": "green"},
]
PLAYERS = [
    {"index": 1, "label": "Premier plan", "stats": {"coverage_percent": 10.0}},
    {"index": 2, "label": "Arrière-plan", "stats": {"coverage_percent": 25.0}},
]


def fake_match(players=PLAYERS, selected=None):
    return SimpleNamespace(
        id="m1", title="Match", sport="padel", status="ready", match_date=None, duration=None,
        rating=4.2, rallies=3, winners=2, errors=1, coverage=70,
        skills=[dict(s) for s in SKILLS], highlights=[], insights=[], patterns_summary={},
        players=players, selected_player_index=selected, created_at=datetime(2026, 10, 4),
    )


def setup(fake_user, match):
    from backend.api.main import app
    from backend.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: fake_user
    fake_db = make_fake_db({Match: match})
    override_db(app, fake_db)
    return fake_db


def test_choisir_un_joueur_sur_un_match_introuvable(client, fake_user):
    setup(fake_user, None)
    assert client.put("/matches/inconnu/player", json={"index": 1}).status_code == 404


def test_choisir_un_joueur_inconnu_est_refuse(client, fake_user):
    match = fake_match()
    db = setup(fake_user, match)

    response = client.put("/matches/m1/player", json={"index": 7})

    assert response.status_code == 400
    assert match.selected_player_index is None
    db.commit.assert_not_called()


def test_choisir_un_joueur_renvoie_la_vue_de_ce_joueur(client, fake_user):
    match = fake_match()
    db = setup(fake_user, match)

    response = client.put("/matches/m1/player", json={"index": 1})
    body = response.json()

    assert response.status_code == 200
    assert body["selected_player_index"] == 1
    assert body["rating"] == 3.7 and body["coverage"] == 10
    assert body["skills"][1]["score"] == 3.8
    assert match.selected_player_index == 1
    db.commit.assert_called_once()


def test_revenir_a_la_vue_du_match_entier(client, fake_user):
    setup(fake_user, fake_match(selected=1))

    body = client.put("/matches/m1/player", json={"index": None}).json()

    assert body["selected_player_index"] is None
    assert body["rating"] == 4.2 and body["coverage"] == 70


def test_le_detail_applique_le_joueur_choisi(client, fake_user):
    setup(fake_user, fake_match(selected=2))

    body = client.get("/matches/m1").json()

    assert body["selected_player_index"] == 2
    assert body["coverage"] == 25
    assert [p["index"] for p in body["players"]] == [1, 2]


def test_le_detail_sans_joueurs_reste_inchange(client, fake_user):
    setup(fake_user, fake_match(players=None))

    body = client.get("/matches/m1").json()

    assert body["players"] is None and body["rating"] == 4.2



def _deux_matchs():
    choisi = fake_match(selected=1)
    choisi.title = "A"
    autre = fake_match()
    autre.id, autre.title, autre.rating = "m2", "B", 4.3
    return choisi, autre


@patch("backend.api.routes_matches.get_user_matches")
def test_la_liste_utilise_la_note_du_joueur_choisi(mock_service, authenticated_client):
    choisi, autre = _deux_matchs()
    mock_service.return_value = [choisi, autre]

    body = authenticated_client.get("/matches").json()

    assert [m["rating"] for m in body] == [3.7, 4.3]
    assert [m["coverage"] for m in body] == [10, 70]


def test_l_evolution_utilise_la_note_du_joueur_choisi(client, fake_user):
    from backend.api.main import app
    from backend.api.deps import get_current_user

    choisi, autre = _deux_matchs()
    app.dependency_overrides[get_current_user] = lambda: fake_user
    override_db(app, make_fake_db({(Match, "all"): [choisi, autre]}))

    body = client.get("/matches/stats/aggregate").json()

    assert [p["rating"] for p in body["timeline"]] == [3.7, 4.3]
    assert body["summary"]["avg_rating"] == 4.0
    assert body["summary"]["best_match"] == "B"
    mouvement = next(s for s in body["avg_skills"] if s["label"] == "Movement")
    assert mouvement["score"] == 4.4