"""
Tests du regroupement de trajectoires de balle en points par alternance de
sens (vers le filet / vers le fond), avec repli sur l'écart de temps.

Les trajectoires sont construites directement (sans passer par le suivi
ios_tracker), pour tester la logique de regroupement de façon isolée, sans
dépendre du comportement d'association du suivi.
"""
from dataclasses import dataclass, field

from backend.services.rally_builder import build_points, MAX_GAP_SECONDS

@dataclass
class FakeTrajectory:
    """Trajectoire minimale : mêmes attributs que Track (ios_tracker.py)."""
    start_frame: int
    end_frame: int
    trajectory: list = field(default_factory=list)  # [(x, y), ...]


SAMPLE_FPS = 5.0


def frame_to_time(frame_index):
    return frame_index / SAMPLE_FPS


def traj(start_frame, end_frame, x_start, x_end, y=0.5):
    return FakeTrajectory(start_frame=start_frame, end_frame=end_frame, trajectory=[(x_start, y), (x_end, y)])


def test_no_trajectories_gives_no_points():
    assert build_points([], frame_to_time) == []


def test_single_trajectory_is_a_point_with_one_shot():
    points = build_points([traj(0, 1, 0.1, 0.4)], frame_to_time)
    assert len(points) == 1
    assert len(points[0]) == 1
    assert points[0][0].index_in_point == 0


def test_alternating_shots_close_in_time_form_one_point():
    t1 = traj(0, 1, 0.1, 0.4)    # forward (vers le filet)
    t2 = traj(6, 7, 0.9, 0.6)    # backward (vers le fond) -> alternance = vrai echange

    points = build_points([t1, t2], frame_to_time)
    assert len(points) == 1
    assert [s.index_in_point for s in points[0]] == [0, 1]
    assert points[0][0].trend == "forward"
    assert points[0][1].trend == "backward"


def test_same_direction_twice_splits_into_two_points_even_if_close_in_time():
    t1 = traj(0, 1, 0.1, 0.4)   # forward
    t2 = traj(3, 4, 0.5, 0.8)   # forward aussi

    points = build_points([t1, t2], frame_to_time)
    assert len(points) == 2
    assert len(points[0]) == 1 and len(points[1]) == 1


def test_flat_shot_does_not_force_a_split():
    t1 = traj(0, 1, 0.1, 0.4)      # forward
    t2 = traj(6, 7, 0.6, 0.61)    # quasi immobile

    points = build_points([t1, t2], frame_to_time)
    assert len(points) == 1


def test_trajectories_far_apart_in_time_always_split_even_if_alternating():
    t1 = traj(0, 1, 0.1, 0.4)      # forward, fin = 0.2s
    t2 = traj(30, 31, 0.9, 0.6)    # backward, debut = 6.0s (ecart 5.8s > 3s)

    points = build_points([t1, t2], frame_to_time)
    assert len(points) == 2


def test_three_alternating_shots_are_indexed_0_1_2_in_one_point():
    t1 = traj(0, 1, 0.05, 0.3)     # forward
    t2 = traj(6, 7, 0.9, 0.6)      # backward
    t3 = traj(12, 13, 0.1, 0.4)    # forward

    points = build_points([t1, t2, t3], frame_to_time)
    assert len(points) == 1
    assert [s.index_in_point for s in points[0]] == [0, 1, 2]


def test_points_are_sorted_chronologically_even_if_input_is_shuffled():
    t_early = traj(0, 1, 0.1, 0.4)
    t_late = traj(30, 31, 0.9, 0.6)

    points = build_points([t_late, t_early], frame_to_time)
    assert len(points) == 2
    assert points[0][0].start_t < points[1][0].start_t