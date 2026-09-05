# Training Workflow Example

Step-by-step example of training a pickleball detection model from scratch.

## Prerequisites

- Python 3.8+
- 10+ GB disk space
- GPU recommended (but not required)
- 5-10 sample pickleball videos

## Complete Workflow

### Step 1: Environment Setup (5 minutes)

```bash
cd training

# Run quick start script
bash scripts/quick_start.sh

# Verify setup
python scripts/test_pipeline.py
```

Expected output:
```
✓ All checks passed! Ready to train.
```

### Step 2: Collect Videos (varies)

Place 5-10 pickleball videos in `data/raw/`:

```bash
# Example structure
data/raw/
├── game1.mp4
├── game2.mp4
├── game3.mp4
└── practice1.mov
```

Tips:
- Use videos with clear visibility
- Include different angles and lighting
- 1-5 minutes per video is sufficient
- Total: 10-30 minutes of footage

### Step 3: Extract Frames (5-10 minutes)

```bash
# Extract at 5 fps (recommended for training)
python scripts/extract_frames.py \
  data/raw/ \
  data/frames/ \
  --fps 5

# Check results
ls data/frames/ | wc -l
# Should see 300-900 frames (5 fps × 60-180 seconds)
```

### Step 4: Annotate Frames (4-8 hours)

This is the most time-consuming step but critical for quality.

#### Option A: CVAT (Recommended)

1. Install CVAT locally or use cvat.ai
2. Create new project: "Pickleball Detection"
3. Add classes: ball, player, paddle, court_line, net, net_post
4. Upload frames from `data/frames/`
5. Annotate all frames:
   - Use rectangle tool
   - Follow ANNOTATION_GUIDE.md
   - Use interpolation for tracking
6. Export in YOLO format
7. Extract to `data/annotations/`

#### Option B: Roboflow

1. Create account at roboflow.com
2. Create new project
3. Upload frames
4. Annotate using web interface
5. Export as "YOLO v8"
6. Download and extract to `data/annotations/`

#### Annotation Tips

- Start with 100 frames for initial model
- Annotate in batches of 20-30 frames
- Take breaks to maintain quality
- Use keyboard shortcuts for speed
- Review annotations before exporting

Expected time:
- 100 frames: 2-3 hours
- 500 frames: 8-12 hours
- 1000 frames: 16-24 hours

### Step 5: Validate Annotations (2 minutes)

```bash
# Check annotation quality
python scripts/validate_annotations.py \
  --images data/frames/ \
  --labels data/annotations/ \
  --classes 6

# Fix any errors reported
```

Expected output:
```
✓ All annotations are valid!
Total images: 300
Annotation coverage: 100%
```

### Step 6: Split Dataset (1 minute)

```bash
# Split into train/val/test (70/20/10)
python scripts/split_dataset.py \
  --images data/frames/ \
  --labels data/annotations/ \
  --output data/ \
  --train 0.7 \
  --val 0.2 \
  --test 0.1

# Verify split
ls data/train/images/ | wc -l  # ~210 images
ls data/val/images/ | wc -l    # ~60 images
ls data/test/images/ | wc -l   # ~30 images
```

### Step 7: Train Model (2-4 hours on GPU, 24-48 hours on CPU)

```bash
# Start training
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --weights models/pretrained/yolov8n.pt

# Training will run for up to 100 epochs
# Early stopping if no improvement for 20 epochs
```

Monitor training:
```bash
# In another terminal, watch progress
tail -f runs/train/pickleball_detector/results.txt

# Or use TensorBoard
tensorboard --logdir runs/train/
```

Expected output:
```
Epoch 1/100: mAP@0.5: 0.234, Loss: 2.456
Epoch 10/100: mAP@0.5: 0.567, Loss: 1.234
Epoch 30/100: mAP@0.5: 0.823, Loss: 0.567
Epoch 45/100: mAP@0.5: 0.891, Loss: 0.345
Early stopping at epoch 65 (no improvement for 20 epochs)

Best model: runs/train/pickleball_detector/weights/best.pt
Final mAP@0.5: 0.891
```

### Step 8: Validate Model (5 minutes)

```bash
# Run validation on test set
python scripts/validate.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml
```

Expected output:
```
VALIDATION RESULTS
==================
Overall Metrics:
  mAP@0.5:      0.891
  mAP@0.5:0.95: 0.654
  Precision:    0.876
  Recall:       0.845

Per-Class Metrics (mAP@0.5):
  ball:         0.923
  player:       0.912
  paddle:       0.867
  court_line:   0.845
  net:          0.901
  net_post:     0.889

Speed Metrics:
  Inference:   145.3 ms
  ✓ Meets < 200ms inference target
```

### Step 9: Convert to Core ML (5 minutes)

```bash
# Convert with quantization
python scripts/convert_to_coreml.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml \
  --output models/exported/

# Check output
ls -lh models/exported/
# PickleballDetector_v1.mlmodel (~6-8 MB)
```

### Step 10: Deploy to iOS (5 minutes)

```bash
# Copy to iOS project
cp models/exported/PickleballDetector_v1.mlmodel \
   ../Models/Pickleball/

# Open Xcode project
open ../nextmove.xcodeproj

# In Xcode:
# 1. Verify model appears in Project Navigator
# 2. Check it's in "Copy Bundle Resources" build phase
# 3. Build and run app
# 4. Test with sample video
```

### Step 11: Test in App (10 minutes)

1. Launch app on device or simulator
2. Record or import a pickleball video
3. Start analysis
4. Verify:
   - Frame extraction works
   - Objects are detected
   - Tracking is stable
   - Coaching feedback is generated

Expected results:
- Detection confidence: 0.7-0.9
- Tracking: Stable IDs across frames
- Analysis time: < 2 minutes for 5-minute video
- Coaching: 3-5 actionable insights

## Troubleshooting

### Low Accuracy (mAP < 0.7)

**Causes:**
- Insufficient training data
- Poor annotation quality
- Inadequate training epochs

**Solutions:**
```bash
# Collect more data (aim for 500+ images)
# Improve annotations (review ANNOTATION_GUIDE.md)
# Train longer
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --resume  # Continue from checkpoint
```

### Out of Memory

**Causes:**
- Batch size too large
- GPU memory insufficient

**Solutions:**
```bash
# Edit configs/pickleball_yolo.yaml
# Reduce batch size:
batch: 8  # or 4

# Or use CPU (slower):
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --device cpu
```

### Slow Inference (> 200ms)

**Causes:**
- Model too large
- Device too old

**Solutions:**
```bash
# Already using yolov8n (nano) - smallest model
# Reduce image size in config:
imgsz: 416  # instead of 640

# Or accept slower inference for better accuracy
```

### Poor Detection of Specific Class

**Example:** Ball detection is poor (mAP < 0.7)

**Solutions:**
1. Annotate more ball examples (aim for 200+)
2. Include diverse conditions:
   - Different lighting
   - Different ball colors
   - Motion blur
   - Partial occlusion
3. Retrain with more data

## Iteration Workflow

After initial model:

1. **Test in app** - Identify failure cases
2. **Collect more data** - Focus on failure scenarios
3. **Annotate new data** - Add to existing dataset
4. **Retrain** - Use previous model as starting point
5. **Validate** - Compare with previous version
6. **Deploy** - Update app with new model

Example iteration:
```bash
# Add new frames to data/frames/
# Annotate and add to data/annotations/
# Re-split dataset
python scripts/split_dataset.py \
  --images data/frames/ \
  --labels data/annotations/ \
  --output data/

# Retrain from previous best model
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --weights runs/train/pickleball_detector/weights/best.pt

# Convert new version
python scripts/convert_to_coreml.py \
  --model runs/train/pickleball_detector2/weights/best.pt \
  --config configs/pickleball_yolo.yaml \
  --output models/exported/

# Rename to v2
mv models/exported/PickleballDetector_v1.mlmodel \
   models/exported/PickleballDetector_v2.mlmodel
```

## Timeline Summary

| Step | Time | Can Parallelize |
|------|------|-----------------|
| Setup | 5 min | No |
| Collect videos | Varies | No |
| Extract frames | 10 min | No |
| Annotate | 4-8 hours | Yes (team) |
| Validate annotations | 2 min | No |
| Split dataset | 1 min | No |
| Train model | 2-4 hours | No |
| Validate model | 5 min | No |
| Convert to Core ML | 5 min | No |
| Deploy to iOS | 5 min | No |
| Test in app | 10 min | No |

**Total time:** 6-12 hours (mostly annotation)

With a team of 3 annotators: 3-5 hours total

## Next Steps

1. Follow this workflow for pickleball
2. Repeat for soccer (if needed)
3. Iterate based on app testing
4. Collect real-world usage data
5. Continuously improve models

## Resources

- Training logs: `runs/train/pickleball_detector/`
- Validation results: `runs/train/pickleball_detector/weights/best_validation.json`
- Exported models: `models/exported/`
- Documentation: `README.md`, `ANNOTATION_GUIDE.md`
