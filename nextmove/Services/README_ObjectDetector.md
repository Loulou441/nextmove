# ObjectDetector Service

## Overview

The `ObjectDetector` service provides object detection capabilities for video frame analysis using Apple's Vision framework and Core ML models. It identifies game elements (ball, player, paddle, court lines, net, etc.) in individual video frames with confidence scores and normalized bounding boxes.

## Architecture

### Components

- **ObjectDetector**: Main service class implementing `ObjectDetectorProtocol`
- **ModelManager**: Loads and caches Core ML models
- **Vision Framework**: Apple's CV framework for running Core ML inference
- **Core ML Models**: Sport-specific detection models (pickleball, tennis, padel)

### Detection Pipeline

```
Video Frame → Vision Request → Core ML Inference → Parse Results → Filter by Confidence → Sort by Confidence → Detection Objects
```

## Features

### Core Functionality

1. **Multi-Sport Support**: Loads sport-specific models via `SportType` parameter
2. **Confidence Filtering**: Filters detections below configurable threshold (default 0.3)
3. **Normalized Coordinates**: Returns bounding boxes in 0-1 range for resolution independence
4. **Sorted Results**: Returns detections sorted by confidence (highest first)
5. **Performance Optimized**: Targets < 200ms per frame on iPhone 12+
6. **Request Caching**: Caches Vision requests to avoid repeated model loading

### Supported Object Classes

**Pickleball**:
- Ball
- Player
- Paddle
- Court Line
- Net
- Net Post

## Usage

### Basic Detection

```swift
// Initialize with model manager
let modelManager = ModelManager()
let detector = ObjectDetector(modelManager: modelManager)

// Detect objects in a frame
let detections = try await detector.detect(in: frame, sportType: .pickleball)

// Process detections
for detection in detections {
    print("Detected \(detection.objectClass) with confidence \(detection.confidence)")
    print("Bounding box: \(detection.boundingBox)")
}
```

### Custom Confidence Threshold

```swift
// Use higher threshold for more precise detections
let detector = ObjectDetector(
    modelManager: modelManager,
    confidenceThreshold: 0.5
)

let detections = try await detector.detect(in: frame, sportType: .pickleball)
```

### Cache Management

```swift
// Release cached Vision requests to free memory
detector.releaseCache()
```

## Implementation Details

### Coordinate System Conversion

Vision framework uses bottom-left origin (0,0), while standard graphics use top-left origin. The ObjectDetector automatically converts coordinates:

```
Vision:    (0,0) = bottom-left, (1,1) = top-right
Standard:  (0,0) = top-left,    (1,1) = bottom-right
```

Conversion formula:
```swift
standardY = 1.0 - visionY - height
```

### Detection Structure

Each `Detection` object contains:
- `id`: Unique identifier (UUID)
- `objectClass`: Type of detected object
- `boundingBox`: Normalized CGRect (0-1 range)
- `confidence`: Float (0.0-1.0)
- `frameNumber`: Frame index in video
- `timestamp`: CMTime timestamp

### Performance Characteristics

- **Target Latency**: < 200ms per frame on iPhone 12+
- **Model Size**: < 10MB (quantized)
- **Memory Usage**: < 100MB during inference
- **Compute Units**: Uses all available (CPU, GPU, Neural Engine)

## Error Handling

### Error Types

1. **ModelLoadingError**: Model not found, incompatible version, compilation failed
2. **DetectionError**: Inference failure, invalid input

### Graceful Degradation

- Returns empty array if no objects detected (not an error)
- Logs warnings for performance issues (> 200ms)
- Continues processing even with low-confidence detections

## Testing

### Unit Tests

Located in `nextmoveTests/ObjectDetectorTests.swift`:

- Detection output structure validation
- Confidence threshold filtering
- Detection sorting by confidence
- Sport-specific model loading
- Error handling
- Performance validation
- Bounding box normalization
- Cache management

### Running Tests

```bash
xcodebuild test -scheme nextmove -destination 'platform=iOS Simulator,name=iPhone 15'
```

## Requirements Validation

This implementation validates the following requirements:

- **2.1-2.10**: Object Detection (all object classes, confidence scores, performance)
- **14.1-14.5**: Vision Framework Integration
- **17.2, 17.6**: Multi-Sport Support
- **23.1-23.7**: Error Handling and Graceful Degradation
- **24.1-24.8**: Performance Optimization

## Model Requirements

### Model Format

- **Format**: Core ML (.mlmodel or .mlmodelc)
- **Input**: 640x640 RGB image
- **Output**: Bounding boxes, class labels, confidence scores
- **Location**: `Models/{Sport}/{ModelName}_v{Version}.mlmodelc`

### Model Naming Convention

```
PickleballDetector_v1.mlmodelc
PickleballDetector_v2.mlmodelc
TennisDetector_v1.mlmodelc
PadelDetector_v1.mlmodelc
```

### Model Directory Structure

```
Models/
  Pickleball/
    PickleballDetector_v1.mlmodelc
    PickleballDetector_v2.mlmodelc
  Tennis/
    TennisDetector_v1.mlmodelc
  Padel/
    PadelDetector_v1.mlmodelc
```

## Future Enhancements

1. **Batch Processing**: Process multiple frames in parallel
2. **GPU Optimization**: Explicit GPU scheduling for better performance
3. **Model Quantization**: Further reduce model size
4. **Adaptive Thresholding**: Adjust confidence threshold based on video quality
5. **Temporal Smoothing**: Use previous frame detections to improve accuracy
6. **Region of Interest**: Focus detection on specific court areas

## Dependencies

- **CoreML**: Apple's machine learning framework
- **Vision**: Apple's computer vision framework
- **AVFoundation**: Video frame handling
- **CoreGraphics**: Image and coordinate manipulation

## Performance Monitoring

The ObjectDetector logs performance metrics:

```
[ObjectDetector] Detected 5 objects in frame 42 (0.156s)
[ObjectDetector] Detection exceeded 200ms target: 0.234s
```

Monitor these logs to identify performance issues and optimize model/code.

## Troubleshooting

### Common Issues

1. **Model Not Found**
   - Verify model file exists in bundle
   - Check model naming convention
   - Ensure model is added to target

2. **Slow Detection (> 200ms)**
   - Check device capabilities
   - Verify model is quantized
   - Monitor memory usage
   - Consider reducing input resolution

3. **Low Detection Accuracy**
   - Adjust confidence threshold
   - Verify video quality
   - Check lighting conditions
   - Retrain model with more data

4. **Memory Issues**
   - Call `releaseCache()` periodically
   - Monitor memory warnings
   - Reduce batch size
   - Use quantized models

## References

- [Vision Framework Documentation](https://developer.apple.com/documentation/vision)
- [Core ML Documentation](https://developer.apple.com/documentation/coreml)
- [VNCoreMLRequest Guide](https://developer.apple.com/documentation/vision/vncoremlrequest)
- [Object Detection Best Practices](https://developer.apple.com/documentation/vision/recognizing_objects_in_live_capture)
