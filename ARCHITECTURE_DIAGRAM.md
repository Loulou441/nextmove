# LLM Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         nextmove App                            │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    RecordingViewModel                      │ │
│  │                                                            │ │
│  │  • Manages UI state                                       │ │
│  │  • Coordinates analysis                                   │ │
│  │  • Reports progress                                       │ │
│  └────────────────────────┬──────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   AnalysisPipeline                         │ │
│  │                                                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │ │
│  │  │VideoProcessor│→ │ObjectDetector│→ │  ObjectTracker  │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────────┐  ┌──────────────────────────────────┐  │ │
│  │  │   Feature    │→ │   EnhancedCoachingEngine         │  │ │
│  │  │  Extractor   │  │                                  │  │ │
│  │  └──────────────┘  │  ┌────────────┐  ┌───────────┐  │  │ │
│  │                    │  │  Coaching  │  │    LLM    │  │  │ │
│  │                    │  │   Engine   │  │  Service  │  │  │ │
│  │                    │  │  (Base)    │  │           │  │  │ │
│  │                    │  └────────────┘  └───────────┘  │  │ │
│  │                    │         │              │         │  │ │
│  │                    │         └──────┬───────┘         │  │ │
│  │                    │                │                 │  │ │
│  │                    │         Fallback/Enhance         │  │ │
│  │                    └──────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │  ConfigurationManager  │
                   │                        │
                   │  • Loads .env file     │
                   │  • Manages API keys    │
                   │  • Provides config     │
                   └────────────────────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │    OpenAI API          │
                   │  (or compatible)       │
                   │                        │
                   │  • gpt-4o-mini         │
                   │  • gpt-4o              │
                   │  • gpt-4               │
                   └────────────────────────┘
```

## Data Flow

### 1. Video Analysis Flow

```
Video File
    │
    ▼
VideoProcessor (extract frames)
    │
    ▼
ObjectDetector (detect ball, players)
    │
    ▼
ObjectTracker (track across frames)
    │
    ▼
FeatureExtractor (compute metrics)
    │
    ▼
EnhancedCoachingEngine
    │
    ├─────────────────────┬─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
Base Coaching      LLM Available?        No API Key
(always runs)           │                     │
    │                   ▼                     │
    │            LLM Enhancement              │
    │                   │                     │
    └───────────────────┴─────────────────────┘
                        │
                        ▼
                Coaching Feedback
                        │
                        ▼
                  GameAnalysis
                        │
                        ▼
                    UI Display
```

### 2. Configuration Loading Flow

```
App Launch
    │
    ▼
ConfigurationManager.shared
    │
    ├─────────────┬─────────────┬─────────────┐
    │             │             │             │
    ▼             ▼             ▼             ▼
.env file   Info.plist   Environment   Defaults
(dev)       (prod)       Variables     (fallback)
    │             │             │             │
    └─────────────┴─────────────┴─────────────┘
                        │
                        ▼
            Merged Configuration
                        │
                        ▼
                  LLMService
```

### 3. LLM Request Flow

```
Performance Features
    │
    ▼
EnhancedCoachingEngine
    │
    ├─── Check API Key ───┐
    │                     │
    ▼                     ▼
API Key Present      No API Key
    │                     │
    ▼                     │
Format Request            │
    │                     │
    ▼                     │
LLMService                │
    │                     │
    ▼                     │
OpenAI API                │
    │                     │
    ├─── Success ────┐    │
    │                │    │
    ▼                ▼    ▼
Parse Response   Error   Fallback
    │                │    │
    └────────────────┴────┘
                │
                ▼
        Enhanced Feedback
```

## Component Responsibilities

### ConfigurationManager
- **Purpose**: Centralized configuration management
- **Responsibilities**:
  - Load API credentials from multiple sources
  - Provide safe defaults
  - Handle missing configuration gracefully
- **Dependencies**: None
- **Used by**: LLMService, EnhancedCoachingEngine

### LLMService
- **Purpose**: Communication with OpenAI-compatible APIs
- **Responsibilities**:
  - Format requests
  - Handle authentication
  - Parse responses
  - Error handling and retries
- **Dependencies**: ConfigurationManager
- **Used by**: EnhancedCoachingEngine

### EnhancedCoachingEngine
- **Purpose**: Generate coaching feedback with optional LLM enhancement
- **Responsibilities**:
  - Always generate base feedback (fallback)
  - Optionally enhance with LLM
  - Merge LLM and base insights
  - Handle LLM failures gracefully
- **Dependencies**: CoachingEngine, LLMService
- **Used by**: AnalysisPipeline

### AnalysisPipeline
- **Purpose**: Orchestrate complete video analysis
- **Responsibilities**:
  - Coordinate all analysis stages
  - Report progress
  - Handle cancellation
  - Return complete GameAnalysis
- **Dependencies**: All analysis components
- **Used by**: ViewModels

## Error Handling Strategy

```
┌─────────────────────────────────────────┐
│         Error Occurs                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Error Type?   │
         └────────┬───────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
Missing Key   API Error   Network Error
    │             │             │
    ▼             ▼             ▼
Use Base     Retry Once    Retry Once
Coaching         │             │
    │            ▼             ▼
    │       Still Fails?  Still Fails?
    │            │             │
    │            ▼             ▼
    │       Use Base      Use Base
    │       Coaching      Coaching
    │            │             │
    └────────────┴─────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Log Error     │
         │  Continue      │
         │  Analysis      │
         └────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────┐
│         API Key Storage                 │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
.env file    Info.plist    Keychain
(dev only)   (build-time)  (future)
    │             │             │
    │             │             │
    ▼             ▼             ▼
.gitignore   Build Config  Encrypted
Protected    Variables     Storage
    │             │             │
    └─────────────┴─────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Never in Code  │
         │ Never in Git   │
         │ Never in Logs  │
         └────────────────┘
```

## Performance Characteristics

### Without LLM
```
Video (5 min) → Analysis Pipeline → Results
                     ~60-90s
```

### With LLM
```
Video (5 min) → Analysis Pipeline → LLM Request → Results
                     ~60-90s          ~1-3s       ~63-93s
                                   (10-15% overhead)
```

### Parallel Processing (Future)
```
Video → Frame Extraction
            │
            ├─→ Detection → Tracking → Features ─┐
            │                                     │
            └─→ Detection → Tracking → Features ─┤
                                                  │
                                                  ▼
                                            Merge Results
                                                  │
                                                  ▼
                                          LLM Enhancement
                                                  │
                                                  ▼
                                              Results
```

## Deployment Configurations

### Development
```
.env file → ConfigurationManager → LLMService
(local)         (runtime)          (OpenAI)
```

### Staging
```
Environment → ConfigurationManager → LLMService
Variables        (runtime)          (OpenAI)
```

### Production
```
Secure Store → ConfigurationManager → LLMService
(Keychain)        (runtime)          (OpenAI/Azure)
```

## Future Enhancements

1. **Caching Layer**
   ```
   Request → Cache Check → Hit? → Return Cached
                │
                ▼ Miss
           LLM Request → Cache Result → Return
   ```

2. **Streaming Responses**
   ```
   LLM Request → Stream Tokens → Update UI Progressively
   ```

3. **Multi-Model Support**
   ```
   Request → Model Router → [GPT-4, Claude, Gemini]
                                      │
                                      ▼
                              Best Available Model
   ```

4. **Offline Mode**
   ```
   No Network → Local Model → Basic Coaching
                (CoreML)
   ```
