# ModelManager Implementation Guide

## Overview

The `ModelManager` class is responsible for loading, caching, and managing Core ML models for the CV/ML video analysis system. It provides a clean abstraction for model lifecycle management with support for multiple sports and model versions.

## Features

### 1. Model Loading (Requirements 13.1, 13.4)
- Loads Core ML models from the app bundle
- Supports sport-specific model organization:
  - `Models/Pickleball/PickleballDetector_v1.mlmodelc`
  - `Models/Tennis/TennisDetector_v1.mlmodelc`
  - `Models/Padel/PadelDetector_v1.mlmodelc`

### 2. Model Caching (Requirement 13.7)
- Caches loaded models in memory to avoid repeated loading overhead
- Thread-safe cache access using NSLock
- Reduces model loading time for subsequent uses

### 3. Model Validation (Requirement 13.2)
- Validates model compatibility with current iOS version
- Checks model metadata for minimum iOS version requirements
- Throws descriptive errors for incompatible models

### 4. Version Support (Requirements 13.4, 28.1-28.7)
- Supports multiple model versions simultaneously
- Version naming convention: `{Sport}Detector_v{N}`
- Fallback mechanism to previous versions if preferred version fails
- Stores model version metadata with analysis results

### 5. Memory Management (Requirement 13.8)
- Listens for memory warnings from iOS
- Automatically releases cached models on memory pressure
- Manual release via `releaseModels()` method

### 6. Error Handling (Requirement 13.3)
- Comprehensive error types:
  - `modelNotFound`: Model file not in bundle
  - `incompatibleVersion`: iOS version too old
  - `compilationFailed`: Model compilation error
  - `memoryAllocationFailed`: Insufficient memory

## Usage

### Basic Model Loading

```swift
let modelManager = ModelManager()

// Load default version (v1)
let model = try await modelManager.loadModel(for: .pickleball, version: nil)

// Load specific version
let modelV2 = try await modelManager.loadModel(for: .pickleball, version: "v2")
```

### Model Loading with Fallback

```swift
// Try to load v2, fall back to v1 if unavailable
let model = try await modelManager.loadModelWithFallback(
    for: .pickleball,
    preferredVersion: "v2"
)
```

### Memory Management

```swift
// Release all cached models
modelManager.releaseModels()

// Check cached version
if let version = modelManager.getCachedModelVersion(for: .pickleball) {
    print("Cached version: \(version)")
}
```

## Adding Models to the Project

### Directory Structure

Create the following directory structure in your Xcode project:

```
nextmove/
  Models/
    Pickleball/
      PickleballDetector_v1.mlmodelc
      PickleballDetector_v2.mlmodelc
    Tennis/
      TennisDetector_v1.mlmodelc
    Padel/
      PadelDetector_v1.mlmodelc
```

### Steps to Add a Model

1. **Convert your trained model to Core ML format** (see Python training pipeline)

2. **Add to Xcode project:**
   - Drag the `.mlmodel` or `.mlmodelc` file into Xcode
   - Ensure "Copy items if needed" is checked
   - Add to the app target
   - Place in the appropriate sport directory

3. **Verify bundle inclusion:**
   - Select the target in Xcode
   - Go to "Build Phases" → "Copy Bundle Resources"
   - Ensure your model file is listed

4. **Set model metadata** (optional but recommended):
   ```python
   # In your Core ML conversion script
   coreml_model.short_description = "Pickleball object detection model"
   coreml_model.author = "NextMove"
   coreml_model.version = "1.0"
   
   # Set minimum iOS version
   metadata = coreml_model.user_defined_metadata
   metadata["minimumIOSVersion"] = "15.0"
   ```

### Model Naming Convention

- **Base name:** `{Sport}Detector` (e.g., `PickleballDetector`, `TennisDetector`)
- **Version suffix:** `_v{N}` (e.g., `_v1`, `_v2`)
- **Full name:** `{Sport}Detector_v{N}.mlmodelc`

Examples:
- `PickleballDetector_v1.mlmodelc`
- `TennisDetector_v1.mlmodelc`
- `PadelDetector_v1.mlmodelc`

## Model Requirements

### Input Specifications
- **Format:** RGB image
- **Size:** 640x640 pixels (Vision framework handles resizing)
- **Type:** CVPixelBuffer or CGImage

### Output Specifications
- **Bounding boxes:** Array of [x, y, width, height] in normalized coordinates (0-1)
- **Class labels:** Array of object class identifiers
- **Confidence scores:** Array of Float values (0.0-1.0)

### Supported Object Classes

**Pickleball:**
- ball
- player
- paddle
- court_line
- net
- net_post

**Padel:**
- ball
- player
- (court-context classes: field, net, wall, outside-field — trained but unused)

## Performance Considerations

### Model Size
- Target: < 10MB per model (use quantization)
- Quantized models load faster and use less memory
- Trade-off: Slight accuracy reduction for significant size reduction

### Inference Speed
- Target: < 200ms per frame on iPhone 12+
- Use Neural Engine when available (automatic with MLModelConfiguration)
- Batch processing can improve throughput on newer devices

### Memory Usage
- Each loaded model: ~50-100MB in memory
- Cache up to 2-3 models simultaneously
- Release models on memory warnings

## Testing

### Unit Tests

The `ModelManagerTests` suite validates:
- Model loading and caching
- Version compatibility checking
- Error handling
- Memory management
- Thread safety

Run tests:
```bash
xcodebuild test -scheme nextmove -only-testing:nextmoveTests/ModelManagerTests
```

### Integration Testing

Test with actual models:
1. Add a test model to the bundle
2. Run integration tests in `ModelManagerTests.testCompleteModelLoadingWorkflow()`
3. Verify model loads, caches, and releases correctly

## Troubleshooting

### Model Not Found Error

**Problem:** `ModelLoadingError.modelNotFound`

**Solutions:**
1. Verify model file is in the correct directory
2. Check model is added to app target in Xcode
3. Verify model name matches naming convention
4. Check "Copy Bundle Resources" in Build Phases

### Incompatible Version Error

**Problem:** `ModelLoadingError.incompatibleVersion`

**Solutions:**
1. Update model metadata with correct minimum iOS version
2. Use Xcode's Core ML model editor to check compatibility
3. Recompile model with compatible Core ML version

### Compilation Failed Error

**Problem:** `ModelLoadingError.compilationFailed`

**Solutions:**
1. Verify model file is not corrupted
2. Check model format is compatible with Core ML
3. Try recompiling model with latest coremltools
4. Check device has sufficient storage for compilation

### Memory Allocation Failed Error

**Problem:** `ModelLoadingError.memoryAllocationFailed`

**Solutions:**
1. Release other cached models first
2. Use quantized models to reduce memory footprint
3. Implement model swapping strategy for multiple sports
4. Test on devices with more memory

## Future Enhancements

### Planned Features
1. **Remote model loading:** Download models from server
2. **Model updates:** Check for and download newer versions
3. **A/B testing:** Compare performance of different model versions
4. **Model compression:** On-device model compression for storage
5. **Lazy loading:** Load model components on-demand

### Cloud Integration
When cloud processing is added:
1. ModelManager will support remote inference endpoints
2. Fallback to local models on network failure
3. Consistent API regardless of processing location

## References

- Requirements: 13.1-13.8 (Core ML Model Management)
- Requirements: 28.1-28.7 (Model Versioning and Upgrades)
- Design Document: Section "ModelManager"
- Protocol: `ModelManagerProtocol` in `CVMLProtocols.swift`
