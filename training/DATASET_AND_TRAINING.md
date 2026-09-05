# Dataset Strategy & Training Workflow

## Data sourcing

NextMove's detection models are trained via **transfer learning from a
COCO-pretrained YOLO backbone, fine-tuned on publicly available, openly licensed
sports-detection datasets** from Roboflow Universe.

This is a deliberate, standard engineering choice:

- **Transfer learning** lets us reuse the visual features a YOLO backbone learned
  from COCO's ~330k images (edges, textures, the "person" concept), so we need far
  less domain data to reach strong performance.
- **Public datasets** give us a reproducible, verifiable starting point and let us
  ship a working detector without a lengthy in-house data-collection phase. As the
  product matures, real match footage can be layered in to further fine-tune.

> Provenance note: we use openly published datasets and attribute them per their
> licenses (typically CC BY 4.0). Any accuracy figures we report are **measured on
> the dataset's validation split**, not estimated.

### Datasets used

| Sport | Source (Roboflow Universe) | Classes | License | Role |
|---|---|---|---|---|
| Pickleball | `racket-ai/pickleball-iiv9m` v5 | ball, paddle, player (~12k train imgs) | CC BY 4.0 | Fine-tuning target |
| Padel | `yolov8-xo2x7/tennisballtracker-*` (tennis) | ball | — | Transfer source until a padel-specific set is added |

## How to run it

### Option 1 — Local download, train on Kaggle (recommended)

```bash
cd training

# 1. Get a free Roboflow API key: https://app.roboflow.com/settings/api
#    Add it to training/.env  ->  ROBOFLOW_API_KEY=xxxx

# 2. Download the dataset locally (to inspect / version it)
venv/bin/python scripts/download_dataset.py --sport pickleball
```

Then upload `kaggle_train_pickleball.ipynb` to Kaggle, enable **GPU T4**, and run
all cells. Training 100 epochs takes ~2-4 hours on GPU (vs 24-48h on CPU).

### Option 2 — Train locally (slow, CPU/MPS)

```bash
cd training
venv/bin/python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --weights models/pretrained/yolo11n.pt \
  --device cpu
```

## Model choice

- **YOLO11n** — primary. Best-in-class Core ML support, fast enough for our
  offline ~5 fps analysis, `<10MB` after quantization.
- **YOLOv8n** — kept for A/B benchmarking (see `MODEL_RESEARCH_AND_RATIONALE.md`).

## After training

1. Export to Core ML (`best.export(format='coreml', nms=True, imgsz=640)`).
2. Rename to `PickleballDetector_v1.mlpackage`.
3. Drop into `nextmove/Models/Pickleball/` and add to the Xcode target.
4. `ModelManager` loads it automatically.

## Honest framing for reports/demos

Accurate claims you can make:

- "We use transfer learning: a COCO-pretrained YOLO11 backbone fine-tuned on a
  domain-specific pickleball dataset."
- "The model runs fully on-device via Core ML — no server round-trips."
- "Validation mAP@0.5 was **[measured number]** on the dataset's val split."

Avoid claiming you collected/annotated your own footage if you used a public set,
or citing accuracy numbers you haven't actually measured. The real engineering
story (transfer learning + on-device Core ML) is already strong on its own.
