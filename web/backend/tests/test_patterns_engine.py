"""
Tests unitaires pour patterns_engine.py — logique pure, aucune dépendance
(pas de base de données, pas de réseau).
"""
import pandas as pd
import pytest

from patterns_engine import compute_match_patterns


def _make_events(rows: list[dict]) -> pd.DataFrame:
    """Construit un DataFrame d'événements à partir de dicts simplifiés."""
    return pd.DataFrame(rows)


def test_basic_counts():
    """Les compteurs de base (events/winners/shots/errors) doivent être exacts."""
    events = _make_events([
        {"event_type": "SHOT", "phase": "Baseline", "x": 20},
        {"event_type": "WINNER", "phase": "Net", "x": 85},
        {"event_type": "ERROR", "phase": "Transition", "x": 60},
    ])

    result = compute_match_patterns(events, sport="padel")

    assert result["total_events"] == 3
    assert result["total_winners"] == 1
    assert result["total_shots"] == 1
    assert result["total_errors"] == 1


def test_event_type_is_case_insensitive():
    """La casse de event_type (winner/Winner/WINNER) ne doit pas fausser le comptage."""
    events = _make_events([
        {"event_type": "winner", "phase": "Net", "x": 85},
        {"event_type": "Winner", "phase": "Net", "x": 85},
    ])

    result = compute_match_patterns(events, sport="padel")

    assert result["total_winners"] == 2


def test_zone_distribution_uses_sport_specific_labels():
    """Les libellés de zone doivent changer selon le sport (padel vs pickleball)."""
    events = _make_events([{"event_type": "SHOT", "phase": "Net", "x": 90}])

    padel_result = compute_match_patterns(events, sport="padel")
    pickleball_result = compute_match_patterns(events, sport="pickleball")

    assert "Zone du filet" in padel_result["zone_distribution"]
    assert "Zone du filet (Kitchen)" in pickleball_result["zone_distribution"]


def test_unknown_sport_falls_back_to_pickleball_zones():
    """Un sport non reconnu ne doit pas planter — repli sur les zones pickleball."""
    events = _make_events([{"event_type": "SHOT", "phase": "Net", "x": 90}])

    result = compute_match_patterns(events, sport="sport-inexistant")

    assert "Zone du filet (Kitchen)" in result["zone_distribution"]


def test_transition_risk_ratio_high_triggers_high_priority():
    """Beaucoup d'événements en transition -> ratio élevé -> priorité 'Élevée'."""
    events = _make_events([
        {"event_type": "SHOT", "phase": "Transition", "x": 60},
        {"event_type": "SHOT", "phase": "Transition", "x": 60},
        {"event_type": "SHOT", "phase": "Baseline", "x": 20},
    ])

    result = compute_match_patterns(events, sport="padel")

    assert result["transition_risk_ratio"] == pytest.approx(0.67, abs=0.01)
    assert result["priority_level"] == "Élevée"


def test_transition_risk_ratio_low_triggers_low_priority():
    """Peu d'événements en transition -> priorité 'Faible'."""
    events = _make_events([
        {"event_type": "SHOT", "phase": "Baseline", "x": 20},
        {"event_type": "SHOT", "phase": "Baseline", "x": 20},
        {"event_type": "SHOT", "phase": "Baseline", "x": 20},
        {"event_type": "SHOT", "phase": "Baseline", "x": 20},
        {"event_type": "SHOT", "phase": "Transition", "x": 60},
    ])

    result = compute_match_patterns(events, sport="padel")

    assert result["transition_risk_ratio"] == pytest.approx(0.2, abs=0.01)
    assert result["priority_level"] == "Faible"


def test_empty_events_does_not_crash():
    """Un match sans aucun événement détecté ne doit jamais lever d'exception."""
    events = pd.DataFrame(columns=["event_type", "phase", "x"])

    result = compute_match_patterns(events, sport="padel")

    assert result["total_events"] == 0
    assert result["transition_risk_ratio"] == 0
    assert result["priority_level"] == "Faible"


def test_more_errors_than_winners_generates_insight():
    """Plus d'erreurs que de winners doit générer l'insight correspondant."""
    events = _make_events([
        {"event_type": "ERROR", "phase": "Baseline", "x": 20},
        {"event_type": "ERROR", "phase": "Baseline", "x": 20},
        {"event_type": "WINNER", "phase": "Net", "x": 85},
    ])

    result = compute_match_patterns(events, sport="padel")

    assert any("erreurs non forcées" in insight for insight in result["insights"])


def test_good_performance_generates_default_insight():
    """Sans signal négatif particulier (peu d'erreurs, zones équilibrées, peu de
    transition), un insight positif par défaut doit apparaître."""
    events = _make_events([
        {"event_type": "WINNER", "phase": "Baseline", "x": 20},
        {"event_type": "WINNER", "phase": "Baseline", "x": 40},
        {"event_type": "SHOT", "phase": "Baseline", "x": 60},
        {"event_type": "SHOT", "phase": "Baseline", "x": 90},
    ])

    result = compute_match_patterns(events, sport="padel")

    assert any("Bon contrôle" in insight for insight in result["insights"])