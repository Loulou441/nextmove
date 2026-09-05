# Padel Model — Full Guide (Dataset → Train → Ship)

How to build the dedicated padel detector and get it into the iOS app. Padel
uses a Roboflow Universe dataset, so the flow mirrors pickleball/tennis.

> **Dataset.** Plaimaker "padel-tkrqs" on Roboflow Universe (Public Domain):
> https://universe.roboflow.com/plaimaker/padel-tkrqs
> Object detection, ~868 images (780 train / 57 val / 31 test), 6 classes:
> `ball, field, net, outside-field, player, wall`.
> (The sibling project `padel-mhxdf` is a keypoint/pose model and does NOT fit
> our bounding-box detector — don't use it.)

The app only consumes `ball` and `player`; the court-context classes (field,
net, wall, outside-field) are trained too but ignored by the current app.

---

## PART A — Download the dataset (1 minute)

From the `training/` folder:

```bash
# needs a free Roboflow API key in training/.env (ROBOFLOW_API_KEY=...)
python scripts/download_dataset.py --sport padel
```

This writes `data/padel_dataset/` with `train/valid/test` folders and a
`data.yaml`. The script prints the class list so you can confirm `ball` and
`player` are present.

### A2. Fix the labels (REQUIRED for this dataset)

The Roboflow export stores most annotations as **segmentation polygons** mixed
with detection boxes in the same files. YOLO's detection trainer rejects mixed
files and would silently drop ~all images. Convert polygons to boxes first:

```bash
python scripts/seg_to_bbox.py --dataset data/padel_dataset
```

This rewrites every label to a clean detection box (polygon → tight bounding
box). After this, all 780 train / 57 val images load with 0 corrupt.

---

## PART B — Train (GPU strongly recommended)

Use the padel config (which points at `data/padel_dataset`):

```bash
python scripts/train_yolo.py --config configs/padel_yolo.yaml --weights yolo11n.pt
```

- Transfer-learns from COCO-pretrained `yolo11n.pt`, fine-tunes 100 epochs.
- Best weights: `runs/train/padel_detector/weights/best.pt`.
- Note the printed **mAP@0.5 / precision / recall** — those are your honest
  numbers. The `ball` class has the fewest boxes (~468), so expect ball recall
  to be the weakest metric; that's normal for a small fast object.

> On Kaggle: same flow as `KAGGLE_STEP_BY_STEP.md`. Upload `data/padel_dataset`
> as a Kaggle dataset (or re-run the download in-notebook), then
> `train_yolo.py --config configs/padel_yolo.yaml`.

---

## PART C — Export to Core ML and ship

```python
from ultralytics import YOLO
model = YOLO("runs/train/padel_detector/weights/best.pt")
model.export(format="coreml", nms=True, imgsz=640)
```

or use the repo helper: `python scripts/convert_to_coreml.py` (see its `--help`).

Then:

1. Rename the exported package to `PadelDetector_v1.mlpackage`.
2. Drop it in `Models/Padel/` (repo root) **and** in the app bundle folder
   `nextmove/Models/Padel/`.
3. In Xcode, add it to the target's **Copy Bundle Resources**.

`ModelManager` already resolves `SportType.padel` to
`Models/Padel/PadelDetector_v1`. Until the model is present, padel analysis uses
the app's demo/mock path.

---

## Class layout reference

| YOLO class        | Used by app? |
|-------------------|:------------:|
| `0: ball`         | ✅ (mapped to `.ball`)   |
| `1: field`        | ignored      |
| `2: net`          | ignored (`.net` exists but court class differs) |
| `3: outside-field`| ignored      |
| `4: player`       | ✅ (mapped to `.player`) |
| `5: wall`         | ignored      |

`ObjectDetector.parseObjectClass` maps `ball` and `player` by name and returns
`nil` for the rest, so no Swift changes are needed.
