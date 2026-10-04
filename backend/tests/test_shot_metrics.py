"""
Tests des mesures par coup (vitesse, zone). Données synthétiques uniquement.
"""
from dataclasses import dataclass, field

from backend.services.rally_builder import Shot 
from backend.services.shot_metrics import shot_speed, shot_zone


@dataclass
class FakeTrajectory:
    start_frame: int
    end_frame: int
    trajectory: list = field(default_factory=list)


def make_shot(start_t, end_t, points, index=0, trend="forward"):
    tr = FakeTrajectory(start_frame=0, end_frame=0, trajectory=points)
    return Shot(trajectory=tr, index_in_point=index, start_t=start_t, end_t=end_t, trend=trend)


def fake_phase_for_x(x, sport):
    """Repli simple pour tester shot_zone sans dépendre de cv_pipeline."""
    if x >= 70:
        return "Net"
    if x >= 40:
        return "Transition"
    return "Baseline"


def test_speed_of_a_fast_short_shot():
    shot = make_shot(0.0, 0.5, [(0.1, 0.5), (0.6, 0.5)])
    assert shot_speed(shot) == 1.0


def test_speed_of_a_slow_shot():
    shot = make_shot(0.0, 2.0, [(0.1, 0.5), (0.6, 0.5)])
    assert shot_speed(shot) == 0.25


def test_speed_with_diagonal_movement_uses_euclidean_distance():
    shot = make_shot(0.0, 1.0, [(0.0, 0.0), (0.3, 0.4)])
    assert shot_speed(shot) == 0.5


def test_speed_is_zero_for_a_single_point_trajectory():
    shot = make_shot(0.0, 1.0, [(0.5, 0.5)])
    assert shot_speed(shot) == 0.0


def test_speed_is_zero_for_instantaneous_shot():
    shot = make_shot(1.0, 1.0, [(0.1, 0.5), (0.6, 0.5)])
    assert shot_speed(shot) == 0.0


def test_zone_uses_the_end_of_the_trajectory_not_the_start():
    shot = make_shot(0.0, 1.0, [(0.1, 0.5), (0.8, 0.5)])
    assert shot_zone(shot, fake_phase_for_x, "padel") == "Net"


def test_zone_baseline_for_low_x():
    shot = make_shot(0.0, 1.0, [(0.5, 0.5), (0.2, 0.5)])
    assert shot_zone(shot, fake_phase_for_x, "padel") == "Baseline"