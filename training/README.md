# NextMove Training Pipeline

Python training pipeline for racket-sport object detection models. Supports training YOLO models for pickleball, tennis, and padel, with Core ML conversion for iOS deployment.

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download pretrained YOLO weights
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -P models/pretrained/
```

### 2. Prepare Dataset

```bash
# Extract frames from videos (5 fps)
python scripts/extract_frames.py videos/ data/frames/ --fps 5

# Annotate frames using your preferred tool (see Annotation section)
# Export annotations in YOLO format to data/annotations/

# Split into train/val/test sets
python scripts/split_dataset.py \
  --images data/frames/ \
  --labels data/annotations/ \
  --output data/ \
  --train 0.7 --val 0.2 --test 0.1

# Validate annotations
python scripts/validate_annotations.py \
  --images data/train/images/ \
  --labels data/train/labels/ \
  --classes 6
```

### 3. Train Model

```bash
# Train pickleball detector
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --weights models/pretrained/yolov8n.pt

# Train tennis detector
python scripts/train_yolo.py \
  --config configs/tennis_yolo.yaml \
  --weights models/pretrained/yolov8n.pt

# Train padel detector (download + fix labels first — see PADEL_STEP_BY_STEP.md)
python scripts/download_dataset.py --sport padel
python scripts/seg_to_bbox.py --dataset data/padel_dataset
python scripts/train_yolo.py \
  --config configs/padel_yolo.yaml \
  --weights models/pretrained/yolov8n.pt

# Resume training from checkpoint
python scripts/train_yolo.py \
  --config configs/pickleball_yolo.yaml \
  --resume
```

### 4. Validate Model

```bash
# Validate trained model
python scripts/validate.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml
```

### 5. Convert to Core ML

```bash
# Convert to Core ML with quantization
python scripts/convert_to_coreml.py \
  --model runs/train/pickleball_detector/weights/best.pt \
  --config configs/pickleball_yolo.yaml \
  --output models/exported/

# Copy to iOS project
cp models/exported/PickleballDetector_v1.mlmodel ../Models/Pickleball/
```

## Directory Structure

```
training/
├── configs/              # Training configurations
│   ├── pickleball_yolo.yaml
│   ├── tennis_yolo.yaml
│   └── padel_yolo.yaml
├── data/                 # Dataset
│   ├── raw/             # Original videos
│   ├── frames/          # Extracted frames
│   ├── annotations/     # Annotation files
│   ├── train/           # Training set
│   │   ├── images/
│   │   └── labels/
│   ├── val/             # Validation set
│   └── test/            # Test set
├── models/
│   ├── pretrained/      # Pretrained weights
│   ├── checkpoints/     # Training checkpoints
│   └── exported/        # Core ML models
├── scripts/             # Training scripts
│   ├── extract_frames.py
│   ├── convert_annotations.py
│   ├── split_dataset.py
│   ├── validate_annotations.py
│   ├── train_yolo.py
│   ├── validate.py
│   └── convert_to_coreml.py
└── runs/                # Training runs (auto-generated)
```

## Annotation

### Supported Tools

- **CVAT** (recommended): https://www.cvat.ai/
- **Label Studio**: https://labelstud.io/
- **Roboflow**: https://roboflow.com/
- **LabelImg**: https://github.com/heartexlabs/labelImg

### Annotation Guidelines

#### Pickleball Classes
1. **ball** - The pickleball (small, usually yellow/green)
2. **player** - Any player on court
3. **paddle** - Pickleball paddle
4. **court_line** - Court boundaries and kitchen line
5. **net** - The net
6. **net_post** - Net support posts

#### Padel Classes (Plaimaker padel-tkrqs dataset)
1. **ball** - The padel ball (small, fast)
2. **player** - Any player on court
3. **field / net / wall / outside-field** - court-context classes (trained but
   ignored by the app, which only uses ball + player)

### Quality Guidelines

- Annotate all visible objects, even if partially occluded
- Use tight bounding boxes (minimal padding)
- Be consistent with class labels
- Annotate at least 100 images per class for good results
- Include diverse conditions (lighting, angles, distances)
- Validate annotations before training

### Export Format

Export annotations in **YOLO format**:
- One `.txt` file per image
- Each line: `class_idx x_center y_center width height`
- All values normalized to 0-1 range
- Class indices start from 0

Example:
```
0 0.5 0.3 0.05 0.05    # ball at center-top
1 0.2 0.6 0.15 0.4     # player on left
1 0.8 0.6 0.15 0.4     # player on right
```

## Training Configuration

### Key Parameters

Edit `configs/pickleball_yolo.yaml`, `configs/tennis_yolo.yaml`, or `configs/padel_yolo.yaml`:

```yaml
# Model size (nano for mobile)
model: yolov8n

# Training duration
epochs: 100
batch: 16
patience: 20  # early stopping

# Learning rate
lr0: 0.001
lrf: 0.01

# Data augmentation
fliplr: 0.5   # horizontal flip
mosaic: 1.0   # mosaic augmentation
```

### Performance Targets

- **Inference time**: < 200ms per frame on iPhone 12+
- **Model size**: < 10MB (with quantization)
- **Accuracy (mAP@0.5)**: > 0.85

### GPU vs CPU

Training on GPU is highly recommended:
- GPU: ~2-4 hours for 100 epochs
- CPU: ~24-48 hours for 100 epochs

To use CPU:
```bash
python scripts/train_yolo.py --config configs/pickleball_yolo.yaml --device cpu
```

## Core ML Conversion

### Quantization

Int8 quantization reduces model size by ~75% with minimal accuracy loss:

```bash
# With quantization (recommended)
python scripts/convert_to_coreml.py --model best.pt --config config.yaml

# Without quantization
python scripts/convert_to_coreml.py --model best.pt --config config.yaml --no-quantize
```

### iOS Integration

1. Convert model to Core ML
2. Copy `.mlmodel` file to `Models/Pickleball/`, `Models/Tennis/`, or `Models/Padel/`
3. Add to Xcode project
4. Ensure it's in "Copy Bundle Resources" build phase
5. ModelManager will load it automatically

## Troubleshooting

### Out of Memory

Reduce batch size in config:
```yaml
batch: 8  # or 4
```

### Poor Accuracy

- Collect more training data (aim for 500+ images)
- Improve annotation quality
- Increase training epochs
- Adjust data augmentation
- Try larger model (yolov8s instead of yolov8n)

### Slow Training

- Use GPU if available
- Reduce image size: `imgsz: 416` (instead of 640)
- Reduce workers: `workers: 4`

### Conversion Errors

- Ensure model trained successfully
- Check coremltools version compatibility
- Try without quantization first

## Advanced Usage

### Custom Data Augmentation

Edit config file:
```yaml
degrees: 10.0      # rotation
translate: 0.2     # translation
scale: 0.9         # scale
perspective: 0.001 # perspective warp
```

### Multi-GPU Training

```bash
python scripts/train_yolo.py --config config.yaml --device 0,1,2,3
```

### Transfer Learning

Use your own pretrained weights:
```bash
python scripts/train_yolo.py \
  --config config.yaml \
  --weights path/to/your/model.pt
```

## Model Versioning

When updating models:
1. Train new model
2. Validate performance
3. Convert to Core ML with new version number
4. Keep previous version as fallback
5. Update ModelManager if needed

Example:
```
Models/Pickleball/
├── PickleballDetector_v1.mlmodel  # Current
├── PickleballDetector_v2.mlmodel  # New version
└── README.md
```

## Resources

- **YOLOv8 Docs**: https://docs.ultralytics.com/
- **Core ML Tools**: https://coremltools.readme.io/
- **CVAT Tutorial**: https://opencv.github.io/cvat/docs/
- **Model Zoo**: https://github.com/ultralytics/ultralytics

## Support

For issues or questions:
1. Check validation metrics
2. Review annotation quality
3. Verify dataset split
4. Check training logs in `runs/train/`
5. Validate Core ML conversion

## Next Steps

1. Annotate 100-500 images per sport
2. Train initial model
3. Validate on test set
4. Convert to Core ML
5. Test in iOS app
6. Iterate based on results
