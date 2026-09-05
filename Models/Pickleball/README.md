# Pickleball Detection Models

This directory contains Core ML models for pickleball object detection.

## Expected Models

Place your compiled Core ML models (`.mlmodelc` files) in this directory:

- `PickleballDetector_v1.mlmodelc` - Default/initial version
- `PickleballDetector_v2.mlmodelc` - Updated version (optional)
- `PickleballDetector_v3.mlmodelc` - Future versions (optional)

## Model Specifications

### Input
- **Format:** RGB image
- **Size:** 640x640 pixels
- **Type:** CVPixelBuffer or CGImage

### Output
- **Bounding boxes:** Normalized coordinates [x, y, width, height] (0-1)
- **Class labels:** Object class identifiers
- **Confidence scores:** Float values (0.0-1.0)

### Detected Object Classes
1. `ball` - Pickleball
2. `player` - Player
3. `paddle` - Paddle
4. `court_line` - Court boundary and kitchen lines
5. `net` - Net
6. `net_post` - Net posts

## Performance Targets

- **Inference time:** < 200ms per frame on iPhone 12+
- **Model size:** < 10MB (quantized)
- **Accuracy (mAP@0.5):** > 0.85

## Adding Models

1. Train your model using the Python training pipeline
2. Convert to Core ML format using `convert_to_coreml.py`
3. Copy the `.mlmodelc` file to this directory
4. Add to Xcode project and ensure it's included in the app target
5. Verify the model appears in "Copy Bundle Resources" build phase

## Model Versioning

When updating models:
1. Keep previous versions for fallback support
2. Update version number in filename (e.g., `_v2`, `_v3`)
3. Test new version thoroughly before removing old versions
4. Document changes in model performance and capabilities

## Training Data

Models should be trained on:
- Indoor and outdoor pickleball courts
- Various lighting conditions
- Different camera angles and distances
- Multiple player skill levels
- Various paddle and ball colors

## Notes

- Models are loaded by `ModelManager` class
- Default version (v1) is used when no version is specified
- Models are cached in memory after first load
- Memory warnings trigger automatic model release
