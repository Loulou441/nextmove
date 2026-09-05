# NextMove App - User Flow Guide

## How the App Works: From Video Upload to AI Analysis

This guide explains the complete journey of a video through the NextMove app, from the moment a user uploads it to receiving personalized coaching feedback.

---

## 📱 Step-by-Step User Flow

### Step 1: Video Upload
**What the user does:**
- Opens the app and taps "Upload Video" or "Record New"
- Selects their sport (Pickleball, Tennis, Padel, or Badminton)
- Chooses a video from their photo library or records new footage
- Gives the video a title

**What happens behind the scenes:**
- `VideoImportView` or `RecordingView` handles the UI
- Video is saved to the app's Documents directory (permanent storage)
- `RecordingViewModel.addRecording()` creates a new `GameRecording` object
- Recording metadata is saved to UserDefaults
- Video appears in the Library with "Pending" status

**Technologies used:**
- SwiftUI for UI
- AVFoundation for video handling
- FileManager for storage
- UserDefaults for persistence

---

### Step 2: User Initiates Analysis
**What the user does:**
- Taps "Analyze" button on their uploaded video
- Sees a progress screen with real-time updates

**What happens behind the scenes:**
- `RecordingViewModel.processRecording()` is called
- Recording status changes to "Processing"
- `AnalysisPipeline` is instantiated with all required components
- Progress tracking begins

**Technologies used:**
- Swift async/await for concurrency
- Combine framework for progress updates
- SwiftUI @Published properties for reactive UI

---

### Step 3: Video Processing (Frame Extraction)
**What happens:**
- `VideoProcessor` loads the video file
- Extracts frames at 5 FPS (5 frames per second)
- Converts each frame to CGImage format
- Creates `VideoFrame` objects with timestamps

**Progress shown to user:**
```
"Extracting frames from video..." (0-20%)
```

**Technologies used:**
- AVFoundation (AVAsset, AVAssetReader, AVAssetImageGenerator)
- CoreGraphics for image processing
- CMTime for precise timestamp tracking

**Output:**
- Array of `VideoFrame` objects (e.g., 900 frames for a 3-minute video)

---

### Step 4: Object Detection (Computer Vision)
**What happens:**
- `ObjectDetector` loads the sport-specific CoreML model
  - Pickleball: Detects ball, players, paddle, court lines, net
  - Padel: Detects ball, players (plus court-context classes)
  - Tennis / Badminton: use the tennis detector (ball, players)
- Processes each frame through the ML model
- Identifies objects with bounding boxes and confidence scores
- Creates `Detection` objects for each found object

**Progress shown to user:**
```
"Detecting objects in frames..." (20-50%)
"Processing frame 450/900..."
```

**Technologies used:**
- CoreML for on-device machine learning
- Vision framework for image analysis
- Custom-trained YOLO models (.mlpackage format)

**Output:**
- Array of `Detection` objects with:
  - Object class (ball, player, etc.)
  - Bounding box (normalized coordinates)
  - Confidence score (0.0-1.0)
  - Frame number and timestamp

---

### Step 5: Object Tracking (Temporal Analysis)
**What happens:**
- `ObjectTracker` links detections across frames
- Uses IoU (Intersection over Union) algorithm
- Creates continuous tracks for each object
- Handles occlusions and temporary disappearances

**Progress shown to user:**
```
"Tracking objects across frames..." (50-60%)
```

**Technologies used:**
- Custom tracking algorithms
- Spatial analysis (CGRect intersection)
- Temporal correlation

**Output:**
- Array of `Track` objects containing:
  - Sequence of detections for same object
  - Start/end timestamps
  - Trajectory (path of movement)
  - Average confidence

---

### Step 6: Feature Extraction (Performance Metrics)
**What happens:**
- `FeatureExtractor` analyzes tracks to compute metrics

**Ball Trajectory Analysis:**
- Identifies shot direction (cross-court, down-the-line, middle)
- Estimates shot depth (kitchen, mid-court, baseline)
- Calculates ball speed
- Groups shots into rallies (3-second gap threshold)

**Player Movement Analysis:**
- Maps player positions to court zones (3x3 grid)
- Calculates court coverage percentages
- Measures movement speed
- Identifies recovery positions
- Computes left-right balance

**Performance Issue Detection:**
- Static positioning (staying in one zone too long)
- Depth positioning (too far from kitchen line)
- Coverage imbalance (favoring one side)
- Poor recovery positioning

**Progress shown to user:**
```
"Analyzing performance metrics..." (60-75%)
```

**Technologies used:**
- Mathematical algorithms (distance, speed, trajectory)
- Statistical analysis
- Sport-specific heuristics

**Output:**
- `PerformanceFeatures` object containing:
  - Ball trajectories with characteristics
  - Player movement patterns
  - Court coverage metrics
  - Detected performance issues

---

### Step 7: Coaching Feedback Generation
**What happens:**
- `EnhancedCoachingEngine` generates personalized feedback

**Base Coaching (Always Runs):**
- `CoachingEngine` applies rule-based analysis
- Maps performance issues to coaching insights
- Generates practice suggestions
- Creates quick tips

**LLM Enhancement (Optional):**
- If API key is configured in `.env` file:
  - `LLMService` formats performance data
  - Sends request to OpenAI-compatible API (GPT-4, GPT-4o-mini, etc.)
  - Receives natural language coaching feedback
  - Merges LLM insights with base coaching
- If no API key or request fails:
  - Automatically falls back to base coaching
  - No error shown to user

**Progress shown to user:**
```
"Generating coaching insights..." (75-90%)
```

**Technologies used:**
- Rule-based expert system
- OpenAI API (optional)
- URLSession for HTTP requests
- JSON encoding/decoding
- Fallback strategy pattern

**Output:**
- `CoachingFeedback` object with:
  - Coaching insights (title, description, severity)
  - Practice suggestions (drills, descriptions)
  - Quick tips
  - Next session focus areas

---

### Step 8: Analysis Compilation
**What happens:**
- `AnalysisPipeline` combines all results
- Creates comprehensive `GameAnalysis` object
- Calculates overall performance rating
- Identifies highlights (winners, long rallies, great defense)
- Computes skill ratings (serve, return, movement, etc.)
- Generates statistics (rally count, winners, errors, coverage)

**Progress shown to user:**
```
"Finalizing analysis..." (90-100%)
```

**Technologies used:**
- Data aggregation algorithms
- Statistical computations
- Rating calculations

**Output:**
- Complete `GameAnalysis` object with:
  - Overall rating (0-5.0)
  - Skill ratings breakdown
  - Game statistics
  - Highlights with timestamps
  - Coaching feedback

---

### Step 9: Results Display
**What the user sees:**
- Recording status changes to "Completed"
- Analysis results appear in the app

**Analysis Detail View shows:**

**Overview Tab:**
- Overall performance rating (circular progress)
- Key insights with icons
- Quick stats grid (rallies, winners, errors, coverage)

**Skills Tab:**
- Skill breakdown bars (serve, return, third shot, dinking, volleys, movement)
- Strengths and focus areas cards

**Highlights Tab:**
- Key moments with timestamps
- Tap to jump to that moment in video

**Stats Tab:**
- Detailed statistics
- Rally information
- Attack success rate
- Court coverage percentage

**Video Player:**
- Inline video playback
- Play/pause controls
- Duration display

**Technologies used:**
- SwiftUI for reactive UI
- AVPlayer for video playback
- Charts and progress indicators
- Custom animations

---

## 🔄 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                            │
└─────────────────────────────────────────────────────────────────┘

1. VIDEO UPLOAD
   User selects video → VideoImportView → RecordingViewModel
                                              ↓
                                    Save to Documents/
                                    Create GameRecording
                                              ↓
                                    Show in Library (Pending)

2. ANALYSIS START
   User taps "Analyze" → RecordingViewModel.processRecording()
                                              ↓
                                    AnalysisPipeline.analyze()

3. VIDEO PROCESSING (0-20%)
   AnalysisPipeline → VideoProcessor
                           ↓
                    Extract frames @ 5 FPS
                           ↓
                    [VideoFrame, VideoFrame, ...]
                    (CGImage + timestamp)

4. OBJECT DETECTION (20-50%)
   [VideoFrame...] → ObjectDetector
                           ↓
                    Load CoreML model
                    (PickleballDetector_v1.mlpackage)
                           ↓
                    Process each frame
                           ↓
                    [Detection, Detection, ...]
                    (class, bbox, confidence)

5. OBJECT TRACKING (50-60%)
   [Detection...] → ObjectTracker
                           ↓
                    Link detections across frames
                    (IoU algorithm)
                           ↓
                    [Track, Track, ...]
                    (object trajectory over time)

6. FEATURE EXTRACTION (60-75%)
   [Track...] → FeatureExtractor
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
   Ball Analysis                        Player Analysis
   • Trajectories                       • Court coverage
   • Shot direction                     • Movement speed
   • Shot depth                         • Positioning
   • Ball speed                         • Recovery
   • Rally grouping                     • Balance
        ↓                                      ↓
        └──────────────────┬──────────────────┘
                           ↓
                    PerformanceFeatures
                    + Performance Issues

7. COACHING GENERATION (75-90%)
   PerformanceFeatures → EnhancedCoachingEngine
                                ↓
                    ┌───────────┴───────────┐
                    ↓                       ↓
              Base Coaching          LLM Enhancement
              (CoachingEngine)       (LLMService)
              • Rule-based           • OpenAI API
              • Always runs          • Optional
                    ↓                       ↓
                    └───────────┬───────────┘
                                ↓
                         CoachingFeedback
                         • Insights
                         • Suggestions
                         • Tips

8. ANALYSIS COMPILATION (90-100%)
   All Components → AnalysisPipeline
                           ↓
                    Create GameAnalysis
                    • Overall rating
                    • Skill ratings
                    • Statistics
                    • Highlights
                    • Coaching feedback

9. RESULTS DISPLAY
   GameAnalysis → RecordingViewModel → AnalysisDetailView
                                              ↓
                                    User sees results:
                                    • Overview
                                    • Skills
                                    • Highlights
                                    • Stats
                                    • Video playback
```

---

## 🛠️ Technology Stack Summary

### Frontend (UI)
- **SwiftUI**: Modern declarative UI framework
- **Combine**: Reactive programming for state management
- **AVKit**: Video player controls

### Backend (Analysis)
- **AVFoundation**: Video processing and frame extraction
- **CoreML**: On-device machine learning
- **Vision**: Image analysis framework
- **CoreGraphics**: Image manipulation

### Machine Learning
- **YOLO (You Only Look Once)**: Object detection model
- **Custom-trained models**: Sport-specific detection
- **CoreML format**: Optimized for iOS

### AI Enhancement (Optional)
- **OpenAI API**: GPT-4, GPT-4o-mini for natural language coaching
- **URLSession**: HTTP networking
- **Fallback strategy**: Works without API key

### Data & Storage
- **UserDefaults**: Recording metadata persistence
- **FileManager**: Video file storage
- **Codable**: JSON serialization
- **Documents directory**: Permanent video storage

### Concurrency & Performance
- **Swift async/await**: Modern asynchronous programming
- **Task**: Structured concurrency
- **AsyncStream**: Progress reporting
- **@MainActor**: UI thread safety

---

## ⚡ Performance Characteristics

### Analysis Time
- **3-minute video**: ~60-90 seconds
- **5-minute video**: ~90-150 seconds

### Breakdown:
- Frame extraction: 20% of time
- Object detection: 30% of time (most intensive)
- Object tracking: 10% of time
- Feature extraction: 15% of time
- Coaching generation: 15% of time
- LLM enhancement: +1-3 seconds (if enabled)

### Resource Usage:
- **CPU**: High during detection phase
- **Memory**: ~500MB-1GB peak
- **Storage**: Original video size + metadata (~1KB)
- **Network**: Only for LLM enhancement (optional)

---

## 🔒 Privacy & Security

### Data Storage
- Videos stored locally on device
- No cloud upload required
- User controls all data

### API Keys
- Stored in `.env` file (development)
- Never committed to git
- Optional feature (app works without)

### Analysis
- All CV/ML processing on-device
- No video data sent to servers
- Only performance metrics sent to LLM (if enabled)

---

## 🎯 Key Features

### Multi-Sport Support (racket sports only)
- Pickleball (fully implemented)
- Padel (dedicated model)
- Tennis (dedicated model)
- Badminton (reuses the tennis detector as a transfer stand-in)

### Intelligent Analysis
- Real-time progress updates
- Automatic error handling
- Graceful degradation

### Personalized Coaching
- Rule-based insights (always available)
- AI-enhanced feedback (optional)
- Sport-specific recommendations

### User Experience
- Intuitive interface
- Inline video playback
- Detailed statistics
- Actionable insights

---

## 📊 Example Analysis Output

For a 3-minute pickleball video:

**Statistics:**
- Total Rallies: 45
- Winners: 21
- Errors: 12
- Longest Rally: 8 shots
- Court Coverage: 78%

**Skill Ratings:**
- Serve: 4.2/5.0
- Return: 3.8/5.0
- Third Shot: 3.5/5.0
- Dinking: 4.0/5.0
- Volleys: 3.9/5.0
- Movement: 4.1/5.0

**Key Insights:**
- "Strong serve performance"
- "Focus on third shot consistency"
- "Excellent court coverage"

**Practice Suggestions:**
- "Third Shot Drop Drill: Practice soft drops to the kitchen"
- "Positioning Drill: Work on recovery to center court"

---

## 🚀 Future Enhancements

### Planned Features
1. **Real-time analysis**: Process video as it's being recorded
2. **Comparison mode**: Compare multiple sessions
3. **Social sharing**: Share highlights with friends
4. **Coach mode**: Coaches can review multiple players
5. **Advanced metrics**: Spin detection, shot placement heatmaps
6. **Offline LLM**: On-device language model for coaching

### Technical Improvements
1. **Parallel processing**: Faster analysis using multiple cores
2. **Model optimization**: Smaller, faster ML models
3. **Caching**: Store intermediate results
4. **Streaming**: Progressive analysis display

---

This guide provides a complete understanding of how NextMove transforms raw video footage into actionable coaching insights using computer vision, machine learning, and optional AI enhancement.
