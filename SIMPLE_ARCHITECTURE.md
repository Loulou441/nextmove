# NextMove - Simple Architecture Diagram

## User Flow: Video Upload → AI Analysis → Results

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    👤 USER UPLOADS VIDEO                        │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Video Saved   │
                    │  to Device     │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🤖 AI ANALYSIS PIPELINE                      │
└─────────────────────────────────────────────────────────────────┘

    Step 1: Extract Frames
    ┌──────────────────────┐
    │   VideoProcessor     │  Extract 5 frames/second
    │                      │  
    │   Input: Video       │
    │   Output: 900 frames │
    └──────────┬───────────┘
               │
               ▼
    
    Step 2: Detect Objects
    ┌──────────────────────┐
    │  ObjectDetector      │  Find ball, players, court
    │  (CoreML + YOLO)     │  
    │                      │
    │   Input: Frames      │
    │   Output: Detections │
    └──────────┬───────────┘
               │
               ▼
    
    Step 3: Track Movement
    ┌──────────────────────┐
    │   ObjectTracker      │  Link objects across frames
    │                      │  
    │   Input: Detections  │
    │   Output: Tracks     │
    └──────────┬───────────┘
               │
               ▼
    
    Step 4: Analyze Performance
    ┌──────────────────────┐
    │  FeatureExtractor    │  Calculate metrics
    │                      │  
    │   • Ball speed       │
    │   • Court coverage   │
    │   • Rally count      │
    │   • Shot patterns    │
    └──────────┬───────────┘
               │
               ▼
    
    Step 5: Generate Coaching
    ┌──────────────────────┐
    │  CoachingEngine      │  Create feedback
    │  + LLM (optional)    │  
    │                      │
    │   • Insights         │
    │   • Tips             │
    │   • Drills           │
    └──────────┬───────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    📊 USER SEES RESULTS                         │
│                                                                 │
│   • Overall Rating (4.2/5.0)                                   │
│   • Skill Breakdown (Serve, Return, Movement...)              │
│   • Statistics (45 rallies, 21 winners, 78% coverage)         │
│   • Coaching Tips ("Focus on third shot consistency")         │
│   • Video Playback with Highlights                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack (Simple View)

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (UI)                           │
│                                                                 │
│   SwiftUI - Modern iOS interface                               │
│   AVKit - Video player                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    COMPUTER VISION (CV/ML)                      │
│                                                                 │
│   AVFoundation - Video processing                              │
│   CoreML - Machine learning (on-device)                        │
│   Vision - Image analysis                                      │
│   Custom YOLO Model - Object detection                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    AI COACHING (Optional)                       │
│                                                                 │
│   OpenAI API - GPT-4 for natural language feedback            │
│   Fallback - Rule-based coaching (always works)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         DATA STORAGE                            │
│                                                                 │
│   FileManager - Video files (Documents folder)                 │
│   UserDefaults - Recording metadata                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure (Simplified)

```
nextmove/
│
├── Views/                    # What user sees
│   ├── HomeView.swift
│   ├── LibraryView.swift
│   ├── RecordingView.swift
│   └── AnalysisDetailView.swift
│
├── ViewModels/               # UI logic
│   └── RecordingViewModel.swift
│
├── Models/                   # Data structures
│   ├── GameRecording.swift
│   ├── CVMLModels.swift
│   └── VideoProcessor.swift
│
├── Services/                 # Analysis pipeline
│   ├── AnalysisPipeline.swift      (Orchestrator)
│   ├── ObjectDetector.swift        (Step 2)
│   ├── ObjectTracker.swift         (Step 3)
│   ├── FeatureExtractor.swift      (Step 4)
│   ├── CoachingEngine.swift        (Step 5)
│   └── LLMService.swift            (Optional AI)
│
└── Models/                   # ML models
    └── Pickleball/
        └── PickleballDetector_v1.mlpackage
```

---

## Data Flow (3 Simple Steps)

```
1. VIDEO IN
   ┌─────────┐
   │  Video  │ → User uploads
   └─────────┘

2. ANALYSIS
   ┌─────────┐
   │ Frames  │ → Extract
   └────┬────┘
        │
   ┌────▼────┐
   │Detections│ → Detect objects
   └────┬────┘
        │
   ┌────▼────┐
   │ Tracks  │ → Track movement
   └────┬────┘
        │
   ┌────▼────┐
   │Metrics  │ → Calculate performance
   └────┬────┘
        │
   ┌────▼────┐
   │Coaching │ → Generate feedback
   └─────────┘

3. RESULTS OUT
   ┌─────────┐
   │Analysis │ → User sees insights
   └─────────┘
```

---

## Key Components Explained

### 1. VideoProcessor
**What it does:** Breaks video into individual frames
**Input:** Video file
**Output:** 900 frames (for 3-min video)
**Tech:** AVFoundation

### 2. ObjectDetector
**What it does:** Finds ball, players, court in each frame
**Input:** Frames
**Output:** Bounding boxes + confidence scores
**Tech:** CoreML + YOLO model

### 3. ObjectTracker
**What it does:** Connects same object across frames
**Input:** Detections
**Output:** Continuous tracks (trajectories)
**Tech:** Custom tracking algorithm

### 4. FeatureExtractor
**What it does:** Calculates performance metrics
**Input:** Tracks
**Output:** Stats (speed, coverage, rallies)
**Tech:** Math + sport rules

### 5. CoachingEngine
**What it does:** Creates personalized feedback
**Input:** Performance metrics
**Output:** Tips, drills, insights
**Tech:** Rules + optional AI (GPT-4)

---

## Timeline (3-minute video)

```
0s ────────────────────────────────────────────────────── 90s

0-18s:  Extract frames        ████████░░░░░░░░░░░░░░░░░░
18-45s: Detect objects        ░░░░░░░░████████████░░░░░░
45-54s: Track movement        ░░░░░░░░░░░░░░░░░░░░████░░
54-68s: Extract features      ░░░░░░░░░░░░░░░░░░░░░░░░██
68-81s: Generate coaching     ░░░░░░░░░░░░░░░░░░░░░░░░░░
81-90s: Finalize              ░░░░░░░░░░░░░░░░░░░░░░░░░░

Total: ~90 seconds
```

---

## What Makes It Work

### On-Device Processing
✅ All video analysis happens on your iPhone
✅ No cloud upload needed
✅ Fast and private

### Smart ML Model
✅ Custom-trained for racket sports (pickleball, tennis, padel)
✅ Detects ball, players, court accurately
✅ Runs efficiently on mobile

### Optional AI Enhancement
✅ GPT-4 makes coaching more natural
✅ Works without it (rule-based fallback)
✅ Just add API key to enable

### Real-Time Progress
✅ Shows what's happening
✅ Updates every step
✅ User knows how long to wait

---

## Example Output

**For a 3-minute pickleball video:**

```
📊 Overall Rating: 4.2/5.0

🎯 Statistics:
   • 45 rallies
   • 21 winners
   • 12 errors
   • 78% court coverage

💪 Strengths:
   • Serve (4.2/5.0)
   • Movement (4.1/5.0)

🎓 Focus Areas:
   • Third shot (3.5/5.0)
   • Return (3.8/5.0)

💡 Coaching Tips:
   • "Focus on third shot consistency"
   • "Practice soft drops to the kitchen"
   • "Work on recovery to center court"
```

---

This is the complete architecture in simple terms - easy to understand and explain!
