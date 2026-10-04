"""
Tests du suivi d'objets (port de ObjectTracker.swift, app iOS).
Données synthétiques : aucune vidéo, aucun détecteur, aucun réseau.
"""
from backend.services.ios_tracker import Detection, ball_trajectories, track_detections

def ball(frame, cx, cy, conf=0.6, size=0.02):
    h = size / 2
    return Detection(frame=frame, cls="ball", box=(cx - h, cy - h, cx + h, cy + h), confidence=conf)


def player(frame, cx, cy, conf=0.8):
    return Detection(frame=frame, cls="player", box=(cx - 0.05, cy - 0.1, cx + 0.05, cy + 0.1), confidence=conf)


def balls_only(tracks):
    return [t for t in tracks if t.cls == "ball"]


def test_empty_input_gives_no_tracks():
    assert track_detections([]) == []


def test_overlapping_ball_boxes_form_one_track():
    dets = [ball(i, 0.5 + 0.001 * i, 0.5, size=0.05) for i in range(5)]
    tracks = balls_only(track_detections(dets))
    assert len(tracks) == 1
    assert len(tracks[0].detections) == 5


def test_fast_ball_without_overlap_is_linked_by_distance():
    # deux boîtes de 2 % sans aucun recouvrement, centres à 0,30 : repli par distance (<= 0,4)
    tracks = balls_only(track_detections([ball(0, 0.2, 0.5), ball(1, 0.5, 0.5)]))
    assert len(tracks) == 1
    assert len(tracks[0].detections) == 2


def test_ball_farther_than_0_4_starts_a_new_track():
    tracks = balls_only(track_detections([ball(0, 0.1, 0.5), ball(1, 0.6, 0.5)]))
    assert len(tracks) == 2
    assert [len(t.detections) for t in tracks] == [1, 1]


def test_player_detection_never_joins_a_ball_track():
    dets = [ball(0, 0.5, 0.5, size=0.05), player(1, 0.5, 0.5)]
    tracks = track_detections(dets)
    assert sorted(t.cls for t in tracks) == ["ball", "player"]
    assert all(len(t.detections) == 1 for t in tracks)


def test_gap_over_30_ends_the_track_when_frames_keep_being_processed():
    # un joueur est détecté à chaque image : à l'image 32 l'écart vaut 31 (> 30)
    # sans balle associée -> la piste est terminée, la balle de l'image 33 en crée une nouvelle
    dets = [ball(0, 0.5, 0.5), ball(1, 0.5, 0.5)]
    dets += [player(f, 0.2, 0.7) for f in range(2, 34)]
    dets += [ball(33, 0.5, 0.5)]
    tracks = balls_only(track_detections(dets))
    assert [len(t.detections) for t in tracks] == [2, 1]


def test_ball_reappearing_at_gap_31_is_still_linked_because_matching_comes_first():
    # à l'image 32 l'écart vaut 31 mais l'association a lieu AVANT la terminaison
    dets = [ball(0, 0.5, 0.5), ball(1, 0.5, 0.5)]
    dets += [player(f, 0.2, 0.7) for f in range(2, 33)]
    dets += [ball(32, 0.5, 0.5)]
    tracks = balls_only(track_detections(dets))
    assert len(tracks) == 1
    assert len(tracks[0].detections) == 3


def test_frames_without_any_detection_are_skipped_like_on_ios():
    # aucune détection entre les images 2 et 44 : ces images ne sont pas traitées,
    # donc la piste n'est pas terminée et la balle de l'image 45 la rejoint
    dets = [ball(0, 0.5, 0.5), ball(1, 0.5, 0.5), ball(45, 0.5, 0.5)]
    tracks = balls_only(track_detections(dets))
    assert len(tracks) == 1
    assert len(tracks[0].detections) == 3


def test_new_track_below_min_confidence_is_terminated_immediately():
    dets = [ball(0, 0.5, 0.5, conf=0.2), ball(1, 0.5, 0.5, conf=0.2)]
    tracks = balls_only(track_detections(dets))
    assert [len(t.detections) for t in tracks] == [1, 1]
    assert ball_trajectories(tracks) == []


def test_average_confidence_dropping_below_0_3_ends_the_track():
    # 0,35 puis 0,22 -> moyenne 0,285 < 0,3 : piste terminée avec 2 détections
    dets = [ball(0, 0.5, 0.5, conf=0.35), ball(1, 0.5, 0.5, conf=0.22), ball(2, 0.5, 0.5, conf=0.9)]
    tracks = balls_only(track_detections(dets))
    assert [len(t.detections) for t in tracks] == [2, 1]
    assert len(ball_trajectories(tracks)) == 1


def test_two_balls_are_each_linked_to_their_own_neighbour():
    dets = [
        ball(0, 0.2, 0.5, size=0.05), ball(0, 0.8, 0.5, size=0.05),
        ball(1, 0.21, 0.5, size=0.05), ball(1, 0.79, 0.5, size=0.05),
    ]
    tracks = balls_only(track_detections(dets))
    assert len(tracks) == 2
    assert [len(t.detections) for t in tracks] == [2, 2]


def test_ball_trajectories_keeps_only_ball_tracks_with_two_points_or_more():
    dets = [
        ball(0, 0.5, 0.5), ball(1, 0.5, 0.5),          # piste de balle à 2 points : gardée
        ball(2, 0.05, 0.95),                            # balle isolée (trop loin) : piste à 1 point, écartée
        player(0, 0.3, 0.6), player(1, 0.3, 0.6),       # joueur : jamais une trajectoire de balle
    ]
    kept = ball_trajectories(track_detections(dets))
    assert len(kept) == 1
    assert kept[0].cls == "ball"
    assert len(kept[0].detections) == 2


def test_trajectory_is_the_sequence_of_box_centers():
    tracks = balls_only(track_detections([ball(0, 0.2, 0.5), ball(1, 0.4, 0.6)]))
    (x0, y0), (x1, y1) = tracks[0].trajectory
    assert (round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)) == (0.2, 0.5, 0.4, 0.6)