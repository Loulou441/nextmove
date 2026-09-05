# Model Research & Learning-Paradigm Rationale

This document explains **which computer-vision models we chose for NextMove, why**, and the
reasoning behind our learning paradigm (transfer learning + fine-tuning). It is grounded in
recent literature so the decisions are defensible, not arbitrary.

> Note: all external findings below are paraphrased/summarized from their sources with links
> provided. Content was rephrased for compliance with licensing restrictions.

---

## 1. The Problem, Restated

NextMove analyzes recorded pickleball (and later soccer) footage on-device (iOS / Core ML) to
detect and track:

- **Players** — medium/large, moderate motion
- **Paddles** — small, fast, often occluded by the hand/body
- **Court lines / net / posts** — static structure
- **The ball** — tiny, very fast, frequently blurry or briefly invisible

These object types have very different difficulty profiles, which is the single most important
fact driving our model choices. A one-size-fits-all detector handles players well and the ball
poorly.

---

## 2. Learning Paradigm: Why Transfer Learning + Fine-Tuning

We do **not** train from scratch. We use **transfer learning followed by fine-tuning**.

### The three options

| Paradigm | What it means | Data needed | Fit for us |
|---|---|---|---|
| From scratch | Random init, learn everything | 100k+ images | ❌ Unrealistic for our dataset size |
| Transfer learning (feature extraction) | Reuse pretrained backbone frozen, train only detection head | Hundreds of images | ⚠️ Fast, but weak on unusual classes (paddle) |
| **Fine-tuning** | Start from pretrained weights, keep training all layers at low LR | Hundreds–thousands | ✅ Our choice |

### Why this is the right call

Pretrained YOLO weights come from **COCO** (~330k images, 80 classes). That network already
encodes generic visual primitives — edges, textures, shapes, and a strong notion of "person."
We reuse that knowledge instead of relearning it. Concretely:

- **`player`** overlaps heavily with COCO's `person` class → transfer is almost free.
- **`paddle`, `court_line`, `net`** are novel → fine-tuning adapts the network to them.
- We have a **small, domain-specific dataset** (hundreds of annotated frames), which is exactly
  the regime where transfer learning + fine-tuning shines and from-scratch training fails.

### Where it lives in our code

It's already in the pipeline — it just wasn't labeled:

```bash
# training/scripts/train_yolo.py
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --weights models/pretrained/yolov8n.pt   # <-- THIS is transfer learning
```

Loading `yolov8n.pt` (COCO-pretrained) and calling `.train()` on our data **is fine-tuning on
top of transfer learning**. It is the Ultralytics default behavior when you start from a `.pt`
checkpoint rather than a `.yaml` architecture file.

---

## 3. Detector Choice: YOLO family vs alternatives

### Candidates reviewed

- **YOLO (v8 / v11 / v12 / v26)** — single-stage real-time detectors
- **RT-DETR** — transformer-based real-time detector

### What the literature says

- **RT-DETR: DETRs Beat YOLOs on Real-time Detection** ([arXiv 2304.08069](https://arxiv.org/abs/2304.08069))
  reports strong accuracy and high FPS **on a T4 GPU**. Great for servers, heavier for phones.
- **YOLOv12: Attention-Centric Real-Time Detectors** ([arXiv 2502.12524](https://arxiv.org/html/2502.12524v1))
  claims to beat RT-DETR variants while being faster and using fewer parameters.
- **Comprehensive Benchmark of YOLOv12/YOLO11 and predecessors** ([arXiv 2411.00201](https://arxiv.org/html/2411.00201v4))
  notes older versions vary: some are accurate but weak on **small objects**; others favor speed
  over precision on overlapping objects.
- **"Is the New YOLO Always Better?" v5→v11 multi-domain benchmark** ([arXiv 2502.14314](https://arxiv.org/html/2502.14314v3))
  is the key caution: **the newest version is not automatically best for a given domain.** You
  must benchmark on your own data.

### On-device reality (the deciding factor)

- Ultralytics ships an **official iOS Core ML app + Swift package** with real-time on-device
  inference, supporting **YOLO11** (Core ML NMS) and YOLO26
  ([github.com/ultralytics/yolo-ios-app](https://github.com/ultralytics/yolo-ios-app),
  [Core ML export docs](https://docs.ultralytics.com/integrations/coreml/)).
- A converted **YOLOv8 nano** Core ML model runs ~10 FPS on an iPhone 12
  ([Hugging Face model card](https://huggingface.co/divinetribe/yolov8n-oiv7-coreml)).

Since NextMove analyzes footage **offline at ~5 fps** (not live camera), ~10 FPS on older
hardware is comfortable headroom.

### Decision

**Primary: YOLO11n (nano). Fallback: YOLO11s (small) if accuracy is short.**

Reasons:

1. **Best-in-class Core ML support** and mature tooling (safer than chasing v12/v26).
2. **Nano is fast enough** for our offline ~5 fps analysis on iPhone 12+.
3. Benchmarks warn **newest ≠ best**, so we favor the mature, well-supported YOLO11.
4. Model size stays small (`<10MB` with int8 quantization) — matches our config target.

> Migration note: our current config pins `yolov8n`. YOLOv8 remains a valid, well-supported
> choice. We recommend benchmarking **YOLO11n vs YOLOv8n on our own annotated clips**
> (mAP@0.5 + on-device FPS) before committing, per the multi-domain benchmark's advice.

---

## 4. The Ball Problem: Why a Second, Specialized Model

Standard box detectors (any YOLO size) struggle with a tiny, fast, blurry ball. This is a known,
studied limitation — not a tuning issue.

- **TrackNet** ([arXiv 1907.03698](https://arxiv.org/abs/1907.03698)) — instead of bounding
  boxes, it consumes **several consecutive frames** (640×360) and outputs a **Gaussian heatmap**
  of the ball position. Learning across frames lets it locate the ball even when blurry or briefly
  occluded.
- **TrackNetV4: Motion Attention Maps** ([arXiv 2409.14543](https://arxiv.org/html/2409.14543v1))
  — improves occlusion/low-visibility handling with frame-difference motion cues.
- **Kalman filters on fast tiny objects** ([arXiv 2509.18451](https://arxiv.org/abs/2509.18451))
  — cautions that plain Kalman trackers **drift significantly** on erratic fast balls. So we will
  not rely on Kalman alone for the ball.

**Decision:** treat the ball as a **separate phase-2 model** (TrackNet-style heatmap), feeding
ball trajectory into our `FeatureExtractor`. Do not try to force the YOLO detector to solve it.

---

## 5. Tracking Across Frames

- **SportsTrack / SportsMOT** ([arXiv 2211.07173](https://arxiv.org/abs/2211.07173)) — sports MOT
  dataset + tracker built for motion blur and overlapping bodies.
- **Soccer detection + ByteTrack + homography** ([arXiv 2602.18504](https://arxiv.org/abs/2602.18504))
  — an end-to-end YOLO + ByteTrack pipeline for players/referees/ball plus a top-down radar view.
  This is effectively our soccer blueprint.

**Decision:** **ByteTrack** for multi-player tracking (mature, widely supported). Trajectory
smoothing (not raw Kalman) for the ball.

---

## 6. Final Architecture & Roadmap

We split the problem into specialized models rather than overloading one:

| Target | Model | Paradigm | Phase |
|---|---|---|---|
| Players, paddles, court, net | **YOLO11n** (fallback YOLO11s) | Transfer learning + fine-tuning from COCO | **1 (now)** |
| Player tracking | **ByteTrack** | Algorithmic (no training) | 1–2 |
| Ball detection | **TrackNet-style heatmap** | Trained on ball datasets | **2** |
| Court mapping / heatmap | Homography transform | Geometric | 3 |

### Phased plan

- **Phase 1 (fast win):** Fine-tune YOLO11n on pickleball frames (Kaggle free GPU) → export Core ML
  → drop into `ModelManager` / `ObjectDetector`. Replaces mock detection with real detection.
- **Phase 2 (differentiator):** Add TrackNet-style ball model for reliable ball trajectory.
- **Phase 3:** Add ByteTrack + homography for robust multi-player tracking and the court heat map.

---

## 7. Reproducibility: Exact Training Recipe

```bash
# 1. Start from COCO-pretrained weights (transfer learning)
#    Swap yolov8n.pt -> yolo11n.pt to adopt YOLO11.
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt \
  -P models/pretrained/

# 2. Fine-tune on our annotated pickleball data
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --weights models/pretrained/yolo11n.pt

# 3. Validate
python scripts/validate.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml

# 4. Export to Core ML (int8 quantized) for iOS
python scripts/convert_to_coreml.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml \
  --output models/exported/
```

Key hyperparameters (already in `configs/pickleball_yolo.yaml`), and *why* they suit fine-tuning:

- `lr0: 0.001` — **low** initial LR so we adapt pretrained weights without destroying them.
- `imgsz: 640` — Core ML mobile standard for detection; matches Ultralytics export defaults.
- `mosaic: 1.0`, `fliplr: 0.5`, HSV jitter — augmentation to stretch a small dataset.
- `patience: 20` — early stopping to avoid overfitting the small dataset.

---

## 8. Summary (TL;DR)

- **Transfer learning + fine-tuning**, not from scratch — small dataset, reuse COCO knowledge.
  It's already wired via the `--weights *.pt` flag.
- **YOLO11n** for players/paddles/court/net — best Core ML support, fast enough for offline
  analysis, size-efficient. Benchmark against YOLOv8n on our own clips before locking in.
- **TrackNet-style model** for the ball (phase 2) — box detectors can't reliably catch a tiny
  fast ball; the literature agrees.
- **ByteTrack** for player tracking; avoid relying on Kalman alone for the ball.

## References

- TrackNet — [arXiv 1907.03698](https://arxiv.org/abs/1907.03698)
- TrackNetV4 — [arXiv 2409.14543](https://arxiv.org/html/2409.14543v1)
- RT-DETR — [arXiv 2304.08069](https://arxiv.org/abs/2304.08069)
- YOLOv12 — [arXiv 2502.12524](https://arxiv.org/html/2502.12524v1)
- YOLO11/YOLOv12 benchmark — [arXiv 2411.00201](https://arxiv.org/html/2411.00201v4)
- "Is the New YOLO Always Better?" — [arXiv 2502.14314](https://arxiv.org/html/2502.14314v3)
- Kalman tracking of fast tiny objects — [arXiv 2509.18451](https://arxiv.org/abs/2509.18451)
- SportsMOT / SportsTrack — [arXiv 2211.07173](https://arxiv.org/abs/2211.07173)
- Soccer + ByteTrack + homography — [arXiv 2602.18504](https://arxiv.org/abs/2602.18504)
- Ultralytics Core ML export — [docs](https://docs.ultralytics.com/integrations/coreml/)
- Ultralytics iOS app/Swift package — [GitHub](https://github.com/ultralytics/yolo-ios-app)
