"""
Tests du calcul des compétences par coup. Données synthétiques uniquement.
"""
from dataclasses import dataclass, field

from backend.services.rally_builder import Shot 
from backend.services import skill_scoring as sk


@dataclass
class FakeDetection:
    confidence: float


@dataclass
class FakeTrajectory:
    trajectory: list = field(default_factory=list)
    detections: list = field(default_factory=list)


def make_shot(points, confidences, start_t, end_t, index=0):
    tr = FakeTrajectory(trajectory=points, detections=[FakeDetection(c) for c in confidences])
    return Shot(trajectory=tr, index_in_point=index, start_t=start_t, end_t=end_t, trend="forward")


def fake_phase_for_x(x, sport):
    """Repli simple, mais avec les memes libelles que _PHASE_ZONES selon le
    sport (Kitchen/Service pour le pickleball, Net/Baseline sinon), pour
    rester coherent avec NET_ZONE/BASELINE_ZONE de skill_scoring.py."""
    if sport == "pickleball":
        if x >= 70:
            return "Kitchen"
        if x >= 40:
            return "Transition"
        return "Service"
    if x >= 70:
        return "Net"
    if x >= 40:
        return "Transition"
    return "Baseline"


def test_shot_confidence_is_the_average_of_detections():
    shot = make_shot([(0.1, 0.5), (0.2, 0.5)], [0.4, 0.8], 0.0, 1.0)
    assert round(sk.shot_confidence(shot), 3) == 0.6


def test_shot_confidence_zero_without_detections():
    shot = make_shot([(0.1, 0.5)], [], 0.0, 1.0)
    assert sk.shot_confidence(shot) == 0.0


def test_shot_quality_combines_confidence_and_capped_speed():
    shot = make_shot([(0.05, 0.5), (0.95, 0.5)], [1.0, 1.0], 0.0, 0.9)
    assert round(sk.shot_quality(shot), 3) == round(0.7 * 1.0 + 0.3 * 1.0, 3)


def test_shot_quality_caps_speed_score_above_reference_speed():
    shot = make_shot([(0.0, 0.5), (1.0, 0.5)], [1.0, 1.0], 0.0, 0.1)
    assert round(sk.shot_quality(shot), 3) == round(0.7 * 1.0 + 0.3 * 1.0, 3)


def test_skill_by_shot_index_averages_quality_at_given_position():
    p1 = [make_shot([(0, 0.5), (0.5, 0.5)], [1.0, 1.0], 0.0, 0.5, index=0)]
    p2 = [make_shot([(0, 0.5), (0.5, 0.5)], [0.0, 0.0], 0.0, 0.5, index=0)]
    result = sk.skill_by_shot_index([p1, p2], 0)
    assert round(result, 3) == round((sk.shot_quality(p1[0]) + sk.shot_quality(p2[0])) / 2, 3)


def test_skill_by_shot_index_ignores_points_too_short():
    p1 = [make_shot([(0, 0.5), (0.5, 0.5)], [1.0], 0.0, 0.5, index=0)]
    result = sk.skill_by_shot_index([p1], 1)
    assert result is None


def test_skill_by_zone_filters_on_end_position():
    net_shot = make_shot([(0.1, 0.5), (0.9, 0.5)], [1.0], 0.0, 1.0)
    baseline_shot = make_shot([(0.5, 0.5), (0.1, 0.5)], [1.0], 0.0, 1.0)
    result = sk.skill_by_zone([net_shot, baseline_shot], "Net", fake_phase_for_x, "padel")
    assert round(result, 3) == round(sk.shot_quality(net_shot), 3)


def test_skill_by_zone_none_when_no_match():
    baseline_shot = make_shot([(0.5, 0.5), (0.1, 0.5)], [1.0], 0.0, 1.0)
    assert sk.skill_by_zone([baseline_shot], "Net", fake_phase_for_x, "padel") is None


def test_dinking_requires_slow_speed_and_net_zone():
    fast_net = make_shot([(0.7, 0.5), (0.9, 0.5)], [1.0], 0.0, 0.1)
    slow_net = make_shot([(0.7, 0.5), (0.75, 0.5)], [1.0], 0.0, 1.0)
    result = sk.skill_dinking([fast_net, slow_net], fake_phase_for_x, "pickleball")
    assert round(result, 3) == round(sk.shot_quality(slow_net), 3)


def test_smash_requires_fast_speed_and_net_zone():
    slow_net = make_shot([(0.7, 0.5), (0.75, 0.5)], [1.0], 0.0, 1.0)
    fast_net = make_shot([(0.7, 0.5), (0.95, 0.5)], [1.0], 0.0, 0.05)
    result = sk.skill_smash([slow_net, fast_net], fake_phase_for_x, "padel")
    assert round(result, 3) == round(sk.shot_quality(fast_net), 3)


def test_lob_requires_slow_speed_and_non_net_zone():
    slow_net = make_shot([(0.7, 0.5), (0.75, 0.5)], [1.0], 0.0, 1.0)
    slow_baseline = make_shot([(0.2, 0.5), (0.25, 0.5)], [1.0], 0.0, 1.0)
    result = sk.skill_lob([slow_net, slow_baseline], fake_phase_for_x, "padel")
    assert round(result, 3) == round(sk.shot_quality(slow_baseline), 3)


def test_defense_excludes_the_serve():
    serve_baseline = make_shot([(0.3, 0.5), (0.2, 0.5)], [1.0], 0.0, 1.0, index=0)
    rally_baseline = make_shot([(0.3, 0.5), (0.2, 0.5)], [1.0], 0.0, 1.0, index=1)
    result = sk.skill_defense([serve_baseline, rally_baseline], fake_phase_for_x, "padel")
    assert round(result, 3) == round(sk.shot_quality(rally_baseline), 3)


def test_regularity_is_high_when_speeds_are_consistent():
    same_speed_a = make_shot([(0.0, 0.5), (0.5, 0.5)], [1.0], 0.0, 1.0)
    same_speed_b = make_shot([(0.0, 0.5), (0.5, 0.5)], [1.0], 0.0, 1.0)
    result = sk.skill_regularity([[same_speed_a, same_speed_b]])
    assert result == 1.0


def test_regularity_is_lower_when_speeds_vary_a_lot():
    slow = make_shot([(0.0, 0.5), (0.1, 0.5)], [1.0], 0.0, 1.0)
    fast = make_shot([(0.0, 0.5), (1.0, 0.5)], [1.0], 0.0, 0.1)
    result = sk.skill_regularity([[slow, fast]])
    assert result == 0.0


def test_regularity_none_when_no_point_has_two_shots():
    single = make_shot([(0.0, 0.5), (0.5, 0.5)], [1.0], 0.0, 1.0)
    assert sk.skill_regularity([[single]]) is None


def test_to_five_scale_bounds():
    assert sk.to_five_scale(0.0) == 1.0
    assert sk.to_five_scale(1.0) == 5.0
    assert sk.to_five_scale(0.5) == 3.0


def test_to_five_scale_clips_out_of_range_values():
    assert sk.to_five_scale(-0.5) == 1.0
    assert sk.to_five_scale(1.5) == 5.0