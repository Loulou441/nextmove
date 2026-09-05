# LLM Integration Checklist

Use this checklist to integrate LLM-powered coaching into your nextmove app.

## ✅ Files Created (Done)

- [x] `nextmove/Services/ConfigurationManager.swift`
- [x] `nextmove/Services/LLMService.swift`
- [x] `nextmove/Services/EnhancedCoachingEngine.swift`
- [x] `nextmove/Services/AnalysisPipeline+LLM.swift`
- [x] `.env` and `.env.example`
- [x] `.gitignore`
- [x] Documentation files
- [x] Test files

## 📋 Your Action Items

### 1. Add API Key to .env
- [ ] Get OpenAI API key from https://platform.openai.com/api-keys
- [ ] Edit `.env` file in project root
- [ ] Replace `your_api_key_here` with actual key
- [ ] Save file

```bash
# Edit this file
nano .env

# Change this line:
OPENAI_API_KEY=your_api_key_here
# To:
OPENAI_API_KEY=sk-your-actual-key-here
```

### 2. Add .env to Xcode Project
- [ ] Open `nextmove.xcodeproj` in Xcode
- [ ] Drag `.env` file from Finder into Xcode project navigator
- [ ] In dialog, check "Copy items if needed"
- [ ] Select target: `nextmove`
- [ ] Click "Finish"

### 3. Add New Files to Xcode Target
Add these files to your Xcode project:

**Services** (add to nextmove target):
- [ ] `nextmove/Services/ConfigurationManager.swift`
- [ ] `nextmove/Services/LLMService.swift`
- [ ] `nextmove/Services/EnhancedCoachingEngine.swift`
- [ ] `nextmove/Services/AnalysisPipeline+LLM.swift`

**Tests** (add to nextmoveTests target):
- [ ] `nextmoveTests/LLMServiceTests.swift`
- [ ] `nextmoveTests/ConfigurationManagerTests.swift`

**How to add**:
1. Right-click on `Services` folder in Xcode
2. Select "Add Files to nextmove..."
3. Select the files
4. Ensure correct target is checked
5. Click "Add"

### 4. Update Your Code

Find where you create `AnalysisPipeline`. This is likely in:
- [ ] `RecordingViewModel.swift`
- [ ] Or wherever you initialize the analysis pipeline

**Change from**:
```swift
let pipeline = AnalysisPipeline(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    coachingEngine: CoachingEngine(),
    modelManager: modelManager
)
```

**To**:
```swift
let pipeline = AnalysisPipeline.withLLMCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager,
    useLLM: true
)
```

### 5. Build and Test
- [ ] Build project (⌘B)
- [ ] Fix any compilation errors
- [ ] Run tests (⌘U)
- [ ] Run app on simulator/device
- [ ] Check console for "API Key configured" message

### 6. Test Video Analysis
- [ ] Record or import a pickleball video
- [ ] Run analysis
- [ ] Check console logs for LLM activity
- [ ] Verify coaching feedback is generated
- [ ] Confirm no crashes or errors

### 7. Verify Fallback Behavior
- [ ] Temporarily remove API key from `.env`
- [ ] Run analysis again
- [ ] Verify app still works with rule-based coaching
- [ ] Restore API key

## 🔍 Verification Commands

### Check Configuration
Add this to your app to verify setup:

```swift
// Add to viewDidLoad or similar
let config = ConfigurationManager.shared
print("=== LLM Configuration ===")
print("API Key: \(config.openAIAPIKey != nil ? "✅ Configured" : "❌ Missing")")
print("Base URL: \(config.openAIBaseURL)")
print("Model: \(config.openAIModel)")
print("========================")
```

### Expected Output
```
=== LLM Configuration ===
API Key: ✅ Configured
Base URL: https://api.openai.com/v1
Model: gpt-4o-mini
========================
```

## 🚨 Common Issues

### Issue: "Cannot find 'ConfigurationManager' in scope"
**Solution**: Add `ConfigurationManager.swift` to Xcode target

### Issue: "API Key not configured"
**Solution**: 
1. Check `.env` file exists in project root
2. Verify file is added to Xcode target
3. Restart Xcode

### Issue: Build errors about missing files
**Solution**: Add all new Swift files to Xcode project target

### Issue: Tests fail
**Solution**: Add test files to `nextmoveTests` target

### Issue: "File not found: .env"
**Solution**: 
1. Ensure `.env` is in project root (same level as `.xcodeproj`)
2. Add to Xcode project
3. Check "Copy items if needed"

## 📊 Testing Checklist

### Unit Tests
- [ ] Run `ConfigurationManagerTests`
- [ ] Run `LLMServiceTests`
- [ ] All tests pass

### Integration Tests
- [ ] Analyze video with LLM enabled
- [ ] Analyze video with LLM disabled
- [ ] Analyze video without API key (fallback)
- [ ] All scenarios work correctly

### Manual Testing
- [ ] Check coaching feedback quality
- [ ] Verify response time is acceptable
- [ ] Confirm no crashes or hangs
- [ ] Test with poor network connection

## 🎯 Success Criteria

You're done when:
- ✅ Project builds without errors
- ✅ All tests pass
- ✅ Video analysis works with LLM
- ✅ Fallback works without API key
- ✅ Console shows "API Key configured"
- ✅ Coaching feedback is generated
- ✅ No crashes or errors

## 📚 Reference Documents

- **Quick Start**: `QUICKSTART_LLM.md`
- **Setup Guide**: `README_LLM_SETUP.md`
- **Technical Docs**: `nextmove/Services/README_LLM.md`
- **Code Examples**: `USAGE_EXAMPLE_LLM.swift`
- **Summary**: `LLM_INTEGRATION_SUMMARY.md`

## 💡 Tips

1. **Start Simple**: Get basic integration working first
2. **Test Fallback**: Ensure app works without LLM
3. **Monitor Costs**: Track API usage in OpenAI dashboard
4. **Check Logs**: Console output helps debug issues
5. **Iterate**: Start with gpt-4o-mini, upgrade if needed

## 🔐 Security Reminder

- ⚠️ Never commit `.env` to git
- ⚠️ Never share your API key
- ⚠️ Rotate keys regularly
- ⚠️ Monitor usage for anomalies

## ✨ Optional Enhancements

After basic integration works:
- [ ] Add user setting to enable/disable LLM
- [ ] Add loading indicator during LLM requests
- [ ] Cache LLM responses for similar analyses
- [ ] Add retry logic for failed requests
- [ ] Implement usage tracking/analytics

---

**Need Help?** Check the documentation files or review `USAGE_EXAMPLE_LLM.swift` for code examples.
