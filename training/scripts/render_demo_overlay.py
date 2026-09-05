#!/usr/bin/env python3
"""
Render a NextMove detection-overlay demo clip.

Runs a Core ML detector (the same .mlpackage the iOS app ships) over a video
segment, tracks players across frames to assign stable IDs (player 1, player 2,
...), and draws bounding boxes + labels, producing an annotated MP4.

Usage:
    python render_demo_overlay.py \
        --model ../../nextmove/Models/Padel/PadelDetector_v1.mlpackage \
        --video "/path/to/input.mp4" \
        --out ../../docs/media/demo_padel.mp4 \
        --start 60 --duration 15 --conf 0.35
"""
import argparse
import os
import colorsys

import cv2
import numpy as np
import coremltools as ct
from PIL import Image


def class_colors(names):
    colors = {}
    n = max(len(names), 1)
    for i, name in names.items():
        h = (i / n) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.75, 1.0)
        colors[i] = (int(b * 255), int(g * 255), int(r * 255))  # BGR for OpenCV
    return colors


# Fixed color per court quadrant / player number (BGR).
# 1: back-left, 2: back-right, 3: front-left, 4: front-right
PLAYER_ID_COLORS = {
    1: (255, 128, 0),    # blue
    2: (0, 200, 0),      # green
    3: (0, 200, 255),    # yellow
    4: (200, 0, 255),    # magenta
}


# Fixed anchor points (normalized foot position) for the 4 court quadrants.
# These are constants for a broadcast-angle padel court, so a given player's
# feet always land closest to the SAME anchor -> the id never flickers.
#   1 = far-left    2 = far-right
#   3 = near-left   4 = near-right
# The court split (near vs far) is decided by whether the foot point is above
# or below _NET_Y, so a player is locked to a HALF regardless of x jitter.
_NET_Y = 0.55
PLAYER_ANCHORS = {
    1: (0.36, 0.40),   # far (back) left   — up, left of center
    2: (0.64, 0.40),   # far (back) right  — up, right of center
    3: (0.12, 0.92),   # near (front) left — low, hard left edge
    4: (0.88, 0.92),   # near (front) right— low, hard right edge
}


def _iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return inter / (area_a + area_b - inter + 1e-9)


def _containment(a, b):
    """Fraction of the SMALLER box's area that lies inside the other box."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return inter / (min(area_a, area_b) + 1e-9)


def _dedup_players(player_dets, iou_thr=0.4, contain_thr=0.6):
    """Collapse overlapping boxes on the SAME person via greedy NMS.

    Besides IoU, also merge when one box is largely CONTAINED in a kept box
    (e.g. a small box on a player's paddle/arm sitting inside the body box),
    which plain IoU misses because the small box barely overlaps in area.
    """
    order = sorted(range(len(player_dets)),
                   key=lambda i: player_dets[i][1], reverse=True)
    keep = []
    for i in order:
        box_i = player_dets[i][0]
        dup = any(
            _iou(box_i, player_dets[j][0]) >= iou_thr
            or _containment(box_i, player_dets[j][0]) >= contain_thr
            for j in keep
        )
        if not dup:
            keep.append(i)
    return [player_dets[i] for i in keep]


# --- Fixed 4-anchor assigner ---------------------------------------------
# Each player number is tied to a FIXED court quadrant anchor. Every frame the
# detections are matched to the nearest anchors (each anchor used once), which
# locks a player to the same number as long as they stay in their quadrant.
# There is no temporal state that can drift, so the numbers do not flicker.


class PlayerTracker:
    def __init__(self):
        pass

    def update(self, player_dets):
        """
        Assign each detection to its nearest FIXED court anchor (each anchor
        used at most once), restricted to the detection's own side of the
        court. Fully STATELESS per frame: a given number is drawn at most once
        and only on a real detection, so numbers cannot duplicate, drift, or
        linger as a phantom on the glass.

        Returns a list of (box_xyxy, score, pid) to draw.
        """
        # Keep at most the 4 highest-confidence boxes.
        kept = sorted(range(len(player_dets)),
                      key=lambda i: player_dets[i][1], reverse=True)[:4]

        foots = {}
        for i in kept:
            (x1, y1, x2, y2), _ = player_dets[i]
            foots[i] = ((x1 + x2) / 2.0, y2)

        # All (distance-to-anchor, det_idx, slot_id) pairs, best first.
        # A detection may only claim a slot on its OWN side of the court:
        #   left-of-center detection  -> a left slot  (1 far, 3 near)
        #   right-of-center detection -> a right slot (2 far, 4 near)
        pairs = []
        for i, (fx, fy) in foots.items():
            det_left = fx < 0.5
            for pid, (ax, ay) in PLAYER_ANCHORS.items():
                if (ax < 0.5) != det_left:
                    continue
                # Weight y more than x: the near/far split is the strong signal
                # and keeps back players off the near anchors.
                d = ((fx - ax) ** 2 + 1.6 * (fy - ay) ** 2) ** 0.5
                pairs.append((d, i, pid))
        pairs.sort()

        assigned = {}          # pid -> det_idx
        used_slots, used_dets = set(), set()
        for d, i, pid in pairs:
            if i in used_dets or pid in used_slots:
                continue
            assigned[pid] = i
            used_dets.add(i)
            used_slots.add(pid)

        draw = []
        for pid, i in assigned.items():
            box, score = player_dets[i]
            draw.append((box, score, pid))
        return draw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=float, default=0.0, help="start time (s)")
    ap.add_argument("--duration", type=float, default=15.0, help="clip length (s)")
    ap.add_argument("--conf", type=float, default=0.35, help="confidence threshold")
    ap.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold")
    ap.add_argument("--fps-out", type=float, default=25.0, help="output fps")
    ap.add_argument("--player-conf", type=float, default=0.55,
                    help="higher confidence gate for the 'player' class")
    ap.add_argument("--keep", default="player,ball,field",
                    help="comma-separated class names to draw (others are dropped)")
    args = ap.parse_args()

    keep_names = {k.strip().lower() for k in args.keep.split(",") if k.strip()}

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    print(f"Loading Core ML model: {args.model}")
    model = ct.models.MLModel(args.model)
    meta = dict(model.user_defined_metadata)
    names = {0: "object"}
    if "classes" in meta or "names" in meta:
        raw = meta.get("classes", meta.get("names"))
        try:
            names = eval(raw) if isinstance(raw, str) else raw
        except Exception:
            names = {i: n for i, n in enumerate(str(raw).split(","))}
    print(f"Classes: {names}")
    colors = class_colors(names)

    spec = model.get_spec()
    img_in = spec.description.input[0]
    W = img_in.type.imageType.width or 640
    H = img_in.type.imageType.height or 640
    print(f"Model input size: {W}x{H}")

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"Could not open video: {args.video}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    vw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    start_frame = int(args.start * src_fps)
    n_frames = int(args.duration * src_fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    step = max(int(round(src_fps / args.fps_out)), 1)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(args.out, fourcc, args.fps_out, (vw, vh))

    processed = 0
    tracker = PlayerTracker()

    def draw_box(frame, box_px, label, color):
        x1, y1, x2, y2 = box_px
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    for i in range(n_frames):
        ok, frame = cap.read()
        if not ok:
            break
        if i % step != 0:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb).resize((W, H))
        out = model.predict(
            {"image": pil, "iouThreshold": args.iou, "confidenceThreshold": args.conf}
        )
        conf = np.array(out["confidence"])          # (N, num_classes)
        coords = np.array(out["coordinates"])        # (N, 4) normalized cx,cy,w,h

        player_dets = []   # (box_norm_xyxy, score)
        other_dets = []    # (cid, box_cxcywh, score)

        if conf.ndim == 2 and conf.shape[0] > 0:
            cls_ids = conf.argmax(axis=1)
            cls_scores = conf.max(axis=1)

            # Find field bounds (reject posters/crowd above the court and
            # people standing OUTSIDE the court to the left/right).
            field_top = 0.0
            field_left, field_right = None, None
            for box, cid, score in zip(coords, cls_ids, cls_scores):
                if names.get(int(cid), "").lower() == "field" and score >= args.conf:
                    fcx, fcy, fbw, fbh = box
                    field_top = max(field_top, fcy - fbh / 2)
                    l, r = fcx - fbw / 2, fcx + fbw / 2
                    field_left = l if field_left is None else min(field_left, l)
                    field_right = r if field_right is None else max(field_right, r)

            for box, cid, score in zip(coords, cls_ids, cls_scores):
                name = names.get(int(cid), "").lower()
                if name not in keep_names:
                    continue
                cx, cy, bw, bh = box

                if name == "player":
                    box_bottom = cy + bh / 2
                    is_near = box_bottom >= 0.7
                    # Near players are motion-blurred / cropped at the bottom
                    # edge and score lower, so use a relaxed gate for them and
                    # the strict gate for far players (rejects crowd/posters).
                    gate = min(args.player_conf, 0.45) if is_near else args.player_conf
                    if score < gate:
                        continue
                    # Reject small ghost boxes (glass-pillar / reflection
                    # artifacts). A real player fills a big chunk of the frame,
                    # especially near ones. This kills the phantom left player
                    # without touching the real near-right player at the edge.
                    box_area = bw * bh
                    min_area = 0.02 if is_near else 0.004
                    if box_area < min_area:
                        continue
                    if field_top > 0.0 and box_bottom < field_top - 0.03:
                        continue
                    # Reject players standing OUTSIDE the court's horizontal
                    # span (e.g. a person to the left of the field). A small
                    # margin lets near players who straddle the sideline pass.
                    if field_left is not None:
                        margin = 0.01
                        if cx < field_left - margin or cx > field_right + margin:
                            continue
                    # Kill the phantom on the LEFT GLASS wall. A real player in
                    # the far-left strip (cx < 0.17) is the near-left player,
                    # whose feet sit low in frame (box_bottom >= 0.82). The
                    # glass reflection/person-behind-glass sits higher up, so
                    # drop any far-left box that doesn't reach the near zone.
                    if cx < 0.17 and box_bottom < 0.82:
                        continue
                    if os.environ.get("NM_DEBUG"):
                        print(f"[dbg] player cx={cx:.3f} cy={cy:.3f} "
                              f"bw={bw:.3f} bh={bh:.3f} near={is_near} "
                              f"score={score:.2f}")
                    # Aspect gate rejects poster/crowd blobs, but ONLY for far
                    # (upper, small) players. Near players stand at the bottom
                    # edge and are often wide or cropped, so skip the gate there.
                    aspect = bh / max(bw, 1e-6)
                    if not is_near and aspect < 0.9:
                        continue
                    x1n, y1n = cx - bw / 2, cy - bh / 2
                    x2n, y2n = cx + bw / 2, cy + bh / 2
                    player_dets.append(((x1n, y1n, x2n, y2n), float(score)))
                else:
                    if score < args.conf:
                        continue
                    other_dets.append((int(cid), box, float(score)))

        # Collapse duplicate boxes on the same person, then assign stable ids
        # via the persistent 4-slot tracker.
        player_dets = _dedup_players(player_dets)
        draw_players = tracker.update(player_dets)

        if os.environ.get("NM_DEBUG"):
            parts = []
            for bn, sc, pid in draw_players:
                fcx = (bn[0] + bn[2]) / 2
                parts.append(f"p{pid}@{fcx:.2f},y{bn[1]:.2f}-{bn[3]:.2f}")
            print(f"[f{processed}] " + " | ".join(parts))

        # Draw non-player classes first (field, ball) so player boxes sit on top
        for cid, box, score in other_dets:
            cx, cy, bw, bh = box
            box_px = (int((cx - bw / 2) * vw), int((cy - bh / 2) * vh),
                      int((cx + bw / 2) * vw), int((cy + bh / 2) * vh))
            draw_box(frame, box_px, f"{names.get(cid, cid)} {score:.2f}",
                     colors.get(cid, (0, 255, 0)))

        # Draw players with their static IDs
        for box_norm, score, pid in draw_players:
            x1n, y1n, x2n, y2n = box_norm
            box_px = (int(x1n * vw), int(y1n * vh), int(x2n * vw), int(y2n * vh))
            color = PLAYER_ID_COLORS.get(pid, (0, 255, 0))
            draw_box(frame, box_px, f"player {pid}", color)

        cv2.putText(frame, "NextMove", (16, vh - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        writer.write(frame)
        processed += 1
        if processed % 20 == 0:
            print(f"  rendered {processed} frames...")

    cap.release()
    writer.release()
    print(f"Done. Wrote {processed} frames to {args.out}")


if __name__ == "__main__":
    main()
