# LLM Integration Summary

## What Was Added

Your nextmove app now has LLM-powered coaching feedback using OpenAI-compatible APIs.

## Files Created

### Core Implementation
1. **`nextmove/Services/ConfigurationManager.swift`**
   - Loads API credentials from .env, Info.plist, or environment variables
   - Provides centralized configuration access
   - Safe defaults and graceful handling of missing keys

2. **`nextmove/Services/LLMService.swift`**
   - Communicates with OpenAI-compatible APIs
   - Handles authentication, requests, and responses
   - Comprehensive error handling

3. **`nextmove/Services/EnhancedCoachingEngine.swift`**
   - Extends base CoachingEngine with LLM capabilities
   - Automatic fallback to rule-based coaching
   - Seamless integration with existing pipeline

4. **`nextmove/Services/AnalysisPipeline+LLM.swift`**
   - Convenience factory methods
   - Easy switching between LLM and standard modes

### Configuration Files
5. **`.env`** - Environment variables (your API key goes here)
6. **`.env.example`** - Template for configuration
7. **`.gitignore`** - Ensures .env is never committed
8. **`nextmove/Info.plist`** - App configuration with permissions

### Documentation
9. **`QUICKSTART_LLM.md`** - 5-minute setup guide
10. **`README_LLM_SETUP.md`** - Comprehensive setup documentation
11. **`nextmove/Services/README_LLM.md`** - Technical documentation
12. **`USAGE_EXAMPLE_LLM.swift`** - Code examples

### Tests
13. **`nextmoveTests/LLMServiceTests.swift`** - LLM service tests
14. **`nextmoveTests/ConfigurationManagerTests.swift`** - Configuration tests

## How It Works

```
Video Analysis → Performance Features → Enhanced Coaching Engine
                                              ↓
                                    ┌─────────┴─────────┐
                                    │                   │
                              LLM Available?      No API Key?
                                    │                   │
                                    ↓                   ↓
                            LLM Enhancement      Base Coaching
                                    │                   │
                                    └─────────┬─────────┘
                                              ↓
                                    Coaching Feedback
```

## Key Features

✅ **Automatic Fallback**: Works without API key using rule-based coaching
✅ **Error Resilient**: Never crashes due to LLM issues
✅ **Easy Integration**: Drop-in replacement for existing CoachingEngine
✅ **Secure**: API keys never committed to git
✅ **Flexible**: Supports OpenAI, Azure OpenAI, and compatible APIs
✅ **Cost Effective**: Uses gpt-4o-mini by default (~$0.01-0.03 per video)

## Next Steps

### 1. Add Your API Key (Required)
```bash
# Edit .env file
nano .env

# Add your key
OPENAI_API_KEY=sk-your-actual-key-here
```

### 2. Add .env to Xcode (Required)
1. Open `nextmove.xcodeproj`
2. Drag `.env` into project
3. Check "Copy items if needed"
4. Add to nextmove target

### 3. Update Your Code (Required)
Find where you create AnalysisPipeline and change:

```swift
// OLD
let coachingEngine = CoachingEngine()
let pipeline = AnalysisPipeline(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    coachingEngine: coachingEngine,
    modelManager: modelManager
)

// NEW
let pipeline = AnalysisPipeline.withLLMCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager,
    useLLM: true
)
```

### 4. Test It
Run your app and check console for:
```
✅ API Key configured
Base URL: https://api.openai.com/v1
Model: gpt-4o-mini
```

## Usage Patterns

### Pattern 1: Always Use LLM (with fallback)
```swift
let pipeline = AnalysisPipeline.withLLMCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager,
    useLLM: true  // Falls back automatically if no API key
)
```

### Pattern 2: User Preference
```swift
let useLLM = UserDefaults.standard.bool(forKey: "enableLLMCoaching")
let pipeline = AnalysisPipeline.withLLMCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager,
    useLLM: useLLM
)
```

### Pattern 3: Standard Mode Only
```swift
let pipeline = AnalysisPipeline.withStandardCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager
)
```

## Configuration Options

### OpenAI (Default)
```bash
OPENAI_API_KEY=sk-your-key
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### Azure OpenAI
```bash
OPENAI_API_KEY=your-azure-key
OPENAI_API_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
OPENAI_MODEL=gpt-4
```

### Other Compatible APIs
Any OpenAI-compatible endpoint works (LocalAI, Ollama, etc.)

## Cost Estimation

| Model | Cost per Video | Quality | Speed |
|-------|---------------|---------|-------|
| gpt-4o-mini | $0.01-0.03 | Good | Fast |
| gpt-4o | $0.05-0.10 | Better | Fast |
| gpt-4 | $0.10-0.30 | Best | Moderate |
| gpt-3.5-turbo | $0.005-0.01 | Basic | Fastest |

**Recommended**: `gpt-4o-mini` for best balance

## Security Checklist

- [x] `.env` added to `.gitignore`
- [ ] API key added to `.env` (you need to do this)
- [ ] `.env` file added to Xcode target
- [ ] API key kept secret (never share or commit)
- [ ] Usage monitoring enabled (optional)

## Troubleshooting

### App works but no LLM enhancement?
Check console for "API Key not configured" - add your key to `.env`

### "File not found" error?
Add `.env` to Xcode project target

### API errors?
Verify key is valid on OpenAI dashboard

### Still having issues?
The app will work with rule-based coaching - LLM is optional

## Documentation Reference

- **Quick Start**: `QUICKSTART_LLM.md` (5-minute setup)
- **Setup Guide**: `README_LLM_SETUP.md` (detailed configuration)
- **Technical Docs**: `nextmove/Services/README_LLM.md` (architecture)
- **Code Examples**: `USAGE_EXAMPLE_LLM.swift` (implementation patterns)

## What's Next?

The integration is complete and ready to use. Just add your API key and update your code to use the enhanced pipeline.

The system is designed to be:
- **Safe**: Never crashes, always has fallback
- **Simple**: Minimal code changes required
- **Flexible**: Easy to enable/disable or switch providers
- **Secure**: API keys never exposed or committed

Happy coaching! 🎾
