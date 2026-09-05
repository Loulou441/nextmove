# LLM Integration Setup Guide

## Overview
The nextmove app now supports LLM-enhanced coaching feedback using OpenAI-compatible APIs (OpenAI, Azure OpenAI, or any compatible endpoint).

## Quick Setup

### 1. Create Environment File
Copy the example file and add your API key:

```bash
cp .env.example .env
```

### 2. Configure Your API Key
Edit `.env` and add your credentials:

```bash
# For OpenAI
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# For Azure OpenAI (example)
# OPENAI_API_KEY=your-azure-key
# OPENAI_API_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
# OPENAI_MODEL=gpt-4
```

### 3. Add .env to Xcode
1. Drag `.env` file into your Xcode project
2. In "Add Files" dialog, ensure "Copy items if needed" is checked
3. Add to target: nextmove

### 4. Update Info.plist (Optional)
For production builds, you can add keys to Info.plist instead:

```xml
<key>OPENAI_API_KEY</key>
<string>$(OPENAI_API_KEY)</string>
<key>OPENAI_API_BASE_URL</key>
<string>https://api.openai.com/v1</string>
<key>OPENAI_MODEL</key>
<string>gpt-4o-mini</string>
```

Then set environment variables in Xcode scheme.

## Usage

### Using Enhanced Coaching Engine

```swift
// In your AnalysisPipeline or ViewModel
let enhancedEngine = EnhancedCoachingEngine(useLLM: true)
let feedback = try await enhancedEngine.generateCoaching(
    from: features,
    sportType: .pickleball
)
```

### Fallback Behavior
- If API key is missing, automatically falls back to rule-based coaching
- If LLM request fails, returns base feedback
- No crashes or errors exposed to users

## Supported Providers

### OpenAI
```bash
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo
```

### Azure OpenAI
```bash
OPENAI_API_BASE_URL=https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-DEPLOYMENT
OPENAI_MODEL=gpt-4
```

### Other Compatible APIs
Any OpenAI-compatible API (LocalAI, Ollama with OpenAI compatibility, etc.)

## Security Notes

1. **Never commit `.env` to git** - it's in `.gitignore`
2. For production, use Xcode build configurations or secure key management
3. Consider rate limiting and cost monitoring for API usage
4. The app works without LLM - it's an enhancement, not a requirement

## Testing

Test the configuration:

```swift
let config = ConfigurationManager.shared
print("API Key configured: \(config.openAIAPIKey != nil)")
print("Base URL: \(config.openAIBaseURL)")
print("Model: \(config.openAIModel)")
```

## Troubleshooting

### API Key Not Loading
- Verify `.env` file is in project root
- Check file is added to Xcode target
- Restart Xcode after adding `.env`

### API Errors
- Check API key is valid
- Verify base URL is correct
- Check network connectivity
- Review Xcode console for error messages

### Fallback to Base Engine
This is normal and expected when:
- No API key configured
- API request fails
- Network unavailable
- Rate limit exceeded

The app will continue working with rule-based coaching.
