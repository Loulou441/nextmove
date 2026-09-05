# Quick Start: LLM-Enhanced Coaching

Get your pickleball video analysis working with GPT-powered coaching in 5 minutes.

## Step 1: Get Your API Key

### Option A: OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

### Option B: OpenAI Compatible API
Use any OpenAI-compatible endpoint (Azure OpenAI, LocalAI, etc.)

## Step 2: Configure Environment

Create a `.env` file in your project root:

```bash
# Copy the example
cp .env.example .env

# Edit with your key
nano .env
```

Add your credentials:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

## Step 3: Add to Xcode

1. Open `nextmove.xcodeproj` in Xcode
2. Drag `.env` file into the project navigator
3. In the dialog:
   - ✅ Check "Copy items if needed"
   - ✅ Select target: nextmove
   - Click "Finish"

## Step 4: Update Your Code

Find where you create the `AnalysisPipeline` (likely in a ViewModel):

### Before:
```swift
let pipeline = AnalysisPipeline(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    coachingEngine: CoachingEngine(),  // Old way
    modelManager: modelManager
)
```

### After:
```swift
let pipeline = AnalysisPipeline.withLLMCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager,
    useLLM: true  // Enable LLM
)
```

## Step 5: Test It

Run your app and analyze a video. Check the console for:

```
✅ API Key configured
Base URL: https://api.openai.com/v1
Model: gpt-4o-mini
```

If you see this, you're good to go!

## Troubleshooting

### "API Key not configured"
- Check `.env` file exists in project root
- Verify file is added to Xcode target
- Restart Xcode

### "API Error 401"
- Your API key is invalid
- Check for extra spaces in `.env`
- Verify key is active on OpenAI dashboard

### "Network Error"
- Check internet connection
- Verify base URL is correct
- Check firewall/proxy settings

### App Still Works Without LLM?
Yes! The app automatically falls back to rule-based coaching if:
- No API key configured
- API request fails
- Network unavailable

This is by design - LLM is an enhancement, not a requirement.

## Cost Estimation

Using `gpt-4o-mini` (recommended):
- ~$0.01-0.03 per video analysis
- Very affordable for development and testing

Using `gpt-4`:
- ~$0.10-0.30 per video analysis
- Better quality, higher cost

## Next Steps

- See `README_LLM_SETUP.md` for advanced configuration
- See `USAGE_EXAMPLE_LLM.swift` for code examples
- Check `nextmoveTests/LLMServiceTests.swift` for testing

## Security Reminder

⚠️ Never commit `.env` to git - it's already in `.gitignore`
