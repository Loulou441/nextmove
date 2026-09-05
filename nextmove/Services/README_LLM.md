# LLM Service Documentation

## Overview

The LLM Service provides AI-powered coaching feedback enhancement for video analysis. It integrates with OpenAI-compatible APIs to generate personalized, context-aware coaching insights.

## Architecture

```
┌─────────────────────────────────────────┐
│      AnalysisPipeline                   │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  EnhancedCoachingEngine           │ │
│  │                                   │ │
│  │  ┌─────────────┐  ┌────────────┐ │ │
│  │  │ CoachingEngine│  │ LLMService │ │ │
│  │  │  (Base)     │  │            │ │ │
│  │  └─────────────┘  └────────────┘ │ │
│  │         │               │         │ │
│  │         └───────┬───────┘         │ │
│  │                 │                 │ │
│  │         Fallback/Enhance          │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │ ConfigurationMgr │
        │   (.env file)    │
        └──────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │  OpenAI API      │
        │  (or compatible) │
        └──────────────────┘
```

## Components

### 1. ConfigurationManager
Loads and manages API credentials from multiple sources:
- `.env` file (development)
- Info.plist (production)
- Environment variables (CI/CD)

**Priority**: Environment Variables > Info.plist > .env file

### 2. LLMService
Handles communication with OpenAI-compatible APIs:
- Request formatting
- Authentication
- Error handling
- Response parsing

### 3. EnhancedCoachingEngine
Combines rule-based and LLM-powered coaching:
- Always generates base feedback (fallback)
- Optionally enhances with LLM
- Graceful degradation on errors

## API Endpoints

### Generate Coaching Insights
```swift
func generateCoachingInsights(
    performanceData: String,
    sportType: String,
    temperature: Double = 0.7
) async throws -> String
```

Generates comprehensive coaching feedback from performance metrics.

**Input**: Formatted performance data with issues, severity, confidence
**Output**: Structured coaching feedback (insights, drills, tips, focus areas)

### Enhance Description
```swift
func enhanceCoachingDescription(
    issueType: String,
    metrics: String,
    confidence: Double,
    sportType: String
) async throws -> String
```

Enhances a specific issue description with context-aware language.

**Input**: Issue details and confidence level
**Output**: Plain-language explanation with appropriate confidence qualifiers

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | API authentication key |
| `OPENAI_API_BASE_URL` | No | `https://api.openai.com/v1` | API endpoint URL |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model to use |
| `OPENAI_ORG_ID` | No | - | Organization ID (optional) |

### Supported Models

**Recommended**:
- `gpt-4o-mini` - Fast, affordable, good quality
- `gpt-4o` - Better quality, moderate cost

**Also Supported**:
- `gpt-4` - Highest quality, higher cost
- `gpt-3.5-turbo` - Fastest, lowest cost

## Error Handling

### Error Types

```swift
enum LLMError: Error {
    case missingAPIKey        // No API key configured
    case invalidURL           // Malformed endpoint URL
    case invalidResponse      // Unexpected API response
    case apiError(String)     // API returned error
    case networkError(Error)  // Network/connection issue
}
```

### Fallback Strategy

1. **No API Key**: Automatically use base coaching engine
2. **API Error**: Log error, return base feedback
3. **Network Error**: Retry once, then fallback
4. **Invalid Response**: Use base feedback

**Result**: App never crashes due to LLM issues

## Usage Examples

### Basic Usage
```swift
let pipeline = AnalysisPipeline.withLLMCoaching(
    videoProcessor: videoProcessor,
    objectDetector: objectDetector,
    objectTracker: objectTracker,
    featureExtractor: featureExtractor,
    modelManager: modelManager,
    useLLM: true
)

let analysis = try await pipeline.analyze(
    recording: recording,
    sportType: .pickleball
)
```

### Direct LLM Service
```swift
let llmService = LLMService()

let insights = try await llmService.generateCoachingInsights(
    performanceData: formattedData,
    sportType: "pickleball",
    temperature: 0.7
)
```

### Configuration Check
```swift
let config = ConfigurationManager.shared

if config.openAIAPIKey != nil {
    print("LLM enabled")
} else {
    print("Using rule-based coaching")
}
```

## Performance

### Latency
- LLM request: ~1-3 seconds
- Total analysis: +10-15% overhead
- Async execution: Non-blocking

### Cost (gpt-4o-mini)
- Per video: ~$0.01-0.03
- Per 1000 videos: ~$10-30
- Tokens per request: ~500-1500

### Optimization
- Batch requests (future)
- Cache common patterns (future)
- Streaming responses (future)

## Security

### Best Practices
1. Never commit `.env` to version control
2. Use environment variables in CI/CD
3. Rotate API keys regularly
4. Monitor usage and costs
5. Implement rate limiting

### Production Deployment
```swift
// Use Xcode build configurations
#if DEBUG
    // Load from .env
#else
    // Load from Info.plist or secure storage
#endif
```

## Testing

### Unit Tests
```swift
// Test without API key
let engine = EnhancedCoachingEngine(useLLM: false)

// Test with mock service
let mockService = MockLLMService()
let engine = EnhancedCoachingEngine(
    useLLM: true,
    llmService: mockService
)
```

### Integration Tests
```bash
# Set test API key
export OPENAI_API_KEY=sk-test-key

# Run tests
xcodebuild test -scheme nextmove
```

## Monitoring

### Logging
```swift
// Enable debug logging
let logger = Logger(subsystem: "com.nextmove", category: "LLM")
logger.debug("LLM request: \(request)")
logger.info("LLM response received")
logger.error("LLM error: \(error)")
```

### Metrics to Track
- Request success rate
- Average latency
- Token usage
- Cost per analysis
- Fallback frequency

## Future Enhancements

1. **Streaming Responses**: Real-time feedback generation
2. **Caching**: Store common patterns
3. **Fine-tuning**: Sport-specific models
4. **Multi-language**: Support multiple languages
5. **Batch Processing**: Analyze multiple videos efficiently

## Troubleshooting

### Common Issues

**Issue**: API key not loading
**Solution**: Check file location, Xcode target, restart Xcode

**Issue**: 401 Unauthorized
**Solution**: Verify API key is valid and active

**Issue**: Rate limit exceeded
**Solution**: Implement exponential backoff, upgrade plan

**Issue**: Slow responses
**Solution**: Use faster model (gpt-4o-mini), reduce temperature

## Support

For issues or questions:
1. Check logs in Xcode console
2. Verify configuration with `ConfigurationManager.shared`
3. Test with base coaching engine first
4. Review OpenAI API status page
