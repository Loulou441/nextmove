# Quick Reference Guide

Fast reference for common training pipeline commands.

## Setup

```bash
# Initial setup (run once)
cd training
bash scripts/quick_start.sh

# Verify setup
python scripts/test_pipeline.py
```

## Data Preparation

```bash
# Extract frames from videos
python scripts/extract_frames.py \
  data/raw/ \
  data/frames/ \
  --fps 5

# Validate annotations
python scripts/validate_annotations.py \
  --images data/frames/ \
  --labels data/annotations/ \
  --classes 6

# Split dataset
python scripts/split_dataset.py \
  --images data/frames/ \
  --labels data/annotations/ \
  --output data/
```

## Training

```bash
# Train pickleball model
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml

# Train padel model
python scripts/train_yolo.py \
  --config configs/padel_yolo.yaml

# Resume training
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --resume

# Train on CPU
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --device cpu
```

## Validation

```bash
# Validate model
python scripts/validate.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml
```

## Conversion

```bash
# Convert to Core ML
python scripts/convert_to_coreml.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml \
  --output models/exported/

# Without quantization
python scripts/convert_to_coreml.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml \
  --output models/exported/ \
  --no-quantize
```

## Deployment

```bash
# Copy to iOS project
cp models/exported/PickleballDetector_v1.mlmodel \
   ../Models/Pickleball/

# Open Xcode
open ../nextmove.xcodeproj
```

## File Locations

| Item | Location |
|------|----------|
| Raw videos | `data/raw/` |
| Extracted frames | `data/frames/` |
| Annotations | `data/annotations/` |
| Training data | `data/train/` |
| Validation data | `data/val/` |
| Test data | `data/test/` |
| Pretrained weights | `models/pretrained/` |
| Training checkpoints | `runs/train/*/weights/` |
| Exported models | `models/exported/` |
| Configs | `configs/` |
| Scripts | `scripts/` |

## Key Files

| File | Purpose |
|------|---------|
| `configs/pickleball_yolo.yaml` | Pickleball training config |
| `configs/tennis_yolo.yaml` | Tennis training config |
| `configs/padel_yolo.yaml` | Padel training config |
| `scripts/train_yolo.py` | Training script |
| `scripts/validate.py` | Validation script |
| `scripts/convert_to_coreml.py` | Core ML conversion |
| `README.md` | Full documentation |
| `ANNOTATION_GUIDE.md` | Annotation instructions |
| `WORKFLOW_EXAMPLE.md` | Step-by-step example |

## Common Issues

### Out of Memory
```yaml
# Edit config file
batch: 8  # reduce from 16
```

### Slow Training
```bash
# Use GPU
python scripts/train_yolo.py --config config.yaml --device 0

# Or reduce image size in config
imgsz: 416  # reduce from 640
```

### Poor Accuracy
- Annotate more data (aim for 500+ images)
- Improve annotation quality
- Train longer (increase epochs)

### Model Too Large
```bash
# Use quantization (default)
python scripts/convert_to_coreml.py --model best.pt --config config.yaml
```

## Performance Targets

| Metric | Target | How to Check |
|--------|--------|--------------|
| mAP@0.5 | > 0.85 | `validate.py` |
| Inference time | < 200ms | `validate.py` |
| Model size | < 10MB | `ls -lh models/exported/` |

## Class Indices

### Pickleball (6 classes)
```
0: ball
1: player
2: paddle
3: court_line
4: net
5: net_post
```

### Padel (6 classes, Plaimaker padel-tkrqs)
```
0: ball
1: field
2: net
3: outside-field
4: player
5: wall
```
(the app only uses `ball` and `player`)

## Annotation Format (YOLO)

```
class_idx x_center y_center width height
```

All values normalized to 0-1 range.

Example:
```
0 0.5 0.3 0.05 0.05
1 0.2 0.6 0.15 0.4
```

## Useful Commands

```bash
# Count images
ls data/train/images/ | wc -l

# Check model size
ls -lh models/exported/*.mlmodel

# Monitor training
tail -f runs/train/*/results.txt

# Find best checkpoint
ls -lh runs/train/*/weights/best.pt

# Clean old runs
rm -rf runs/train/exp*
```

## Getting Help

1. Check `README.md` for detailed docs
2. Review `WORKFLOW_EXAMPLE.md` for step-by-step guide
3. Read `ANNOTATION_GUIDE.md` for annotation help
4. Run `python scripts/test_pipeline.py` to verify setup
5. Check training logs in `runs/train/*/`

## Next Steps

1. ✅ Setup complete
2. ⚠️ Annotate data (4-8 hours)
3. ⚠️ Train model (2-4 hours)
4. ⚠️ Validate results
5. ⚠️ Convert to Core ML
6. ⚠️ Deploy to iOS
7. ⚠️ Test in app
