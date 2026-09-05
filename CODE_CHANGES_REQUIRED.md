# Required Code Changes

This document shows the exact code changes you need to make to integrate LLM coaching.

## Change 1: Update Pipeline Initialization

### Location
Find where you create `AnalysisPipeline`. This is likely in:
- `RecordingViewModel.swift`
- Or your main analysis coordinator

### Before (Current Code)
```swift
let videoProcessor = VideoProcessor()
let modelManager = ModelManager()
let objectDetector = ObjectDetector(modelManager: modelManager)
let objectTracker = ObjectTracker()
let featureExtractor = FeatureExtractor()
let coachingEngine = CoachingEngine()  // ← OLD

let pipeline = AnalysisPipeline(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    coachingEngine: coachingEngine,  // ← OLD
    modelManager: modelManager
)
```

### After (New Code)
```swift
let videoProcessor = VideoProcessor()
let modelManager = ModelManager()
let objectDetector = ObjectDetector(modelManager: modelManager)
let objectTracker = ObjectTracker()
let featureExtractor = FeatureExtractor()

// Use factory method with LLM support
let pipeline = AnalysisPipeline.withLLMCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager,
    useLLM: true  // ← NEW: Enable LLM
)
```

### What Changed
- Removed manual `CoachingEngine` creation
- Use `AnalysisPipeline.withLLMCoaching()` factory method
- Added `useLLM: true` parameter

## Change 2: Add Configuration Check (Optional)

### Location
Add to your ViewModel or app initialization

### Code to Add
```swift
func checkLLMConfiguration() {
    let config = ConfigurationManager.shared
    
    if let _ = config.openAIAPIKey {
        print("✅ LLM coaching enabled")
        print("   Model: \(config.openAIModel)")
        print("   Endpoint: \(config.openAIBaseURL)")
    } else {
        print("ℹ️ Using rule-based coaching (no API key)")
    }
}

// Call in viewDidLoad or init
checkLLMConfiguration()
```

## Change 3: Add User Toggle (Optional)

### Location
In your settings view or preferences

### Code to Add
```swift
// In your ViewModel
@AppStorage("enableLLMCoaching") private var enableLLM = true

// When creating pipeline
let pipeline = AnalysisPipeline.withLLMCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager,
    useLLM: enableLLM  // ← Use user preference
)

// In your settings view
Toggle("AI-Enhanced Coaching", isOn: $viewModel.enableLLM)
```

## That's It!

These are the only code changes required. The rest is configuration:

1. Add API key to `.env`
2. Add files to Xcode project
3. Build and run

## Complete Example

Here's a complete ViewModel example:

```swift
import SwiftUI

@MainActor
class RecordingViewModel: ObservableObject {
    @Published var isAnalyzing = false
    @Published var analysisProgress: Double = 0.0
    @Published var currentAnalysis: GameAnalysis?
    
    @AppStorage("enableLLMCoaching") private var enableLLM = true
    
    private var pipeline: AnalysisPipeline?
    
    init() {
        setupPipeline()
        checkConfiguration()
    }
    
    private func setupPipeline() {
        let videoProcessor = VideoProcessor()
        let modelManager = ModelManager()
        let objectDetector = ObjectDetector(modelManager: modelManager)
        let objectTracker = ObjectTracker()
        let featureExtractor = FeatureExtractor()
        
        // NEW: Use LLM-enhanced pipeline
        pipeline = AnalysisPipeline.withLLMCoaching(
            videoProcessor: videoProcessor,
            objectDetector: objectDetector,
            objectTracker: objectTracker,
            featureExtractor: featureExtractor,
            modelManager: modelManager,
            useLLM: enableLLM
        )
    }
    
    private func checkConfiguration() {
        let config = ConfigurationManager.shared
        if config.openAIAPIKey != nil {
            print("✅ LLM enabled (\(config.openAIModel))")
        } else {
            print("ℹ️ Rule-based coaching")
        }
    }
    
    func analyzeRecording(_ recording: GameRecording) async {
        guard let pipeline = pipeline else { return }
        
        isAnalyzing = true
        
        // Monitor progress
        Task {
            for await progress in pipeline.progress {
                analysisProgress = progress.percentage
            }
        }
        
        do {
            let analysis = try await pipeline.analyze(
                recording: recording,
                sportType: .pickleball
            )
            currentAnalysis = analysis
        } catch {
            print("Analysis failed: \(error)")
        }
        
        isAnalyzing = false
    }
}
```

## Verification

After making changes, you should see:

```
✅ LLM enabled (gpt-4o-mini)
Starting analysis...
Progress: frameExtraction - 20%
Progress: objectDetection - 50%
Progress: objectTracking - 65%
Progress: featureExtraction - 80%
Progress: coachingGeneration - 95%
Analysis complete!
```

## Troubleshooting

**Build errors?**
- Add new Swift files to Xcode target
- Clean build folder (⌘⇧K)

**"Cannot find 'AnalysisPipeline.withLLMCoaching'"?**
- Add `AnalysisPipeline+LLM.swift` to project

**"Cannot find 'ConfigurationManager'"?**
- Add `ConfigurationManager.swift` to project

**No LLM enhancement?**
- Check API key in `.env`
- Verify `.env` is in Xcode target
- Restart Xcode
