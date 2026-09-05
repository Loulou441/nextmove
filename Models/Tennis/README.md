# Tennis Detector Model

Place the trained Core ML model here as:

```
Models/Tennis/TennisDetector_v1.mlpackage
```

This model is used for **Tennis** and, as a transfer stand-in, for
**Badminton** (badminton has no dedicated model — it maps to this tennis
detector in `ModelManager`, being the closest trained match: fast small
projectile, net-divided court).

Padel is NOT covered here — it has its own dedicated model
(`Models/Padel/PadelDetector_v1.mlpackage`, trained on the Plaimaker padel
dataset).

## How it's produced

1. Train via `training/configs/tennis_yolo.yaml` (transfer learning from
   COCO-pretrained YOLO11n, fine-tuned on a public tennis dataset).
2. Export to Core ML: `best.export(format='coreml', nms=True, imgsz=640)`.
3. Rename to `TennisDetector_v1.mlpackage` and drop it in this folder.
4. Add it to the Xcode target's "Copy Bundle Resources".

Until this model exists, tennis analysis falls back to the app's demo/mock
analysis path.
