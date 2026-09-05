# Padel Detector Model

Place the trained Core ML model here as:

```
Models/Padel/PadelDetector_v1.mlpackage
```

Padel has a **dedicated** detector (it no longer transfers from the tennis
model). `ModelManager` maps `SportType.padel` to `Models/Padel/PadelDetector_v1`.

## Dataset

Trained on the **Plaimaker "padel-tkrqs"** dataset from Roboflow Universe
(Public Domain): https://universe.roboflow.com/plaimaker/padel-tkrqs

Object detection, ~868 images, 6 classes: `ball, field, net, outside-field,
player, wall`. The app consumes `ball` and `player`; the court-context classes
are trained but ignored by the current app.

## How it's produced

All steps run from the `training/` folder (see `training/PADEL_STEP_BY_STEP.md`
for the full walkthrough).

1. **Download** (needs a free Roboflow API key in `training/.env`):
   ```
   python scripts/download_dataset.py --sport padel
   ```
2. **Train** YOLO11n using the padel config:
   ```
   python scripts/train_yolo.py --config configs/padel_yolo.yaml --weights yolo11n.pt
   ```
3. **Export to Core ML**: `model.export(format='coreml', nms=True, imgsz=640)`.
4. Rename to `PadelDetector_v1.mlpackage` and drop it in this folder.
5. Add it to the Xcode target's "Copy Bundle Resources".

Until this model exists, padel analysis falls back to the app's demo/mock
analysis path.
