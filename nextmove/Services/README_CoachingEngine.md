# CoachingEngine

## Overview

The `CoachingEngine` translates performance metrics from video analysis into human-readable coaching feedback. It implements intelligent issue prioritization, plain-language generation, and confidence-aware messaging to provide actionable insights for players.

**Validates: Requirements 8.1-8.10**

## Features

### 1. Issue Prioritization (Requirement 8.7)

Issues are sorted by severity using impact weights that reflect their significance on performance:

- **Recovery Positioning**: 1.0 (highest impact)
- **Depth Positioning**: 0.9
- **Coverage Imbalance**: 0.8
- **Reaction Timing**: 0.7
- **Side-Specific Timing**: 0.7
- **Static Positioning**: 0.6

The weighted severity score is computed as: `severity × impact_weight`

### 2. Top 5 Selection (Requirement 8.9)

Only the top 5 most significant issues are included in feedback to avoid overwhelming the player. This ensures focus on the most impactful improvements.

### 3. Plain-Language Descriptions (Requirements 8.1-8.4)

Each issue type has a sport-specific template that translates technical metrics into actionable feedback:

- **Static Positioning**: "You tend to stay in the same area for extended periods..."
- **Depth Positioning**: "You are often positioned too far behind the kitchen line..."
- **Reaction Timing**: "You show delayed movement after your opponent contacts the ball..."
- **Coverage Imbalance**: "Your court coverage is stronger on one side than the other..."
- **Side-Specific Timing**: "You are often contacting the ball late on one side..."
- **Recovery Positioning**: "After hitting shots, you tend to stay where you are..."

### 4. Confidence-Aware Language (Requirement 8.8)

The engine adjusts language based on confidence scores:

- **High Confidence (> 0.7)**: Direct statements
  - "You tend to stay in the same area..."
  
- **Medium Confidence (0.6-0.7)**: Qualifying language
  - "You appear to stay in the same area..."
  - "You may be positioned too far..."
  
- **Low Confidence (< 0.6)**: Excluded from feedback

### 5. Practice Suggestions (Requirement 8.5)

Each issue type is mapped to a specific drill with actionable instructions:

| Issue Type | Drill | Description |
|------------|-------|-------------|
| Static Positioning | Shadowing Drill | Practice moving to different court positions without a ball |
| Depth Positioning | Kitchen Line Drill | Practice dinking while maintaining position at the kitchen line |
| Reaction Timing | Split-Step Drill | Practice the split-step timing as opponent contacts the ball |
| Coverage Imbalance | Side-to-Side Drill | Have a partner hit alternating shots to your weaker side |
| Side-Specific Timing | Wall Drill | Practice shots on your weaker side against a wall |
| Recovery Positioning | Recovery Drill | Hit a shot, then immediately return to center position |

### 6. Quick Tips (Requirement 8.6)

Concise, immediately actionable tips for the top 3 issues:

- "Stay on your toes and keep moving"
- "Move forward after your return"
- "Split-step when your opponent contacts the ball"
- "Recover to center after each shot"
- "Keep your paddle up and ready"

### 7. Next Session Focus (Requirement 8.10)

Recommended focus areas for the next practice session based on top issues:

- "Work on court mobility and dynamic positioning"
- "Focus on moving forward to control the net"
- "Practice split-step timing and quick reactions"
- "Improve movement and coverage on your weaker side"
- "Develop earlier contact timing on your weaker side"
- "Build automatic recovery to center position"

## Usage

```swift
let coachingEngine = CoachingEngine()

// Generate coaching feedback from performance features
let feedback = try await coachingEngine.generateCoaching(
    from: performanceFeatures,
    sportType: .pickleball
)

// Access insights
for insight in feedback.insights {
    print("\(insight.title): \(insight.description)")
}

// Access practice suggestions
for suggestion in feedback.practiceSuggestions {
    print("\(suggestion.drill): \(suggestion.description)")
}

// Access quick tips
for tip in feedback.quickTips {
    print("💡 \(tip)")
}

// Access next session focus
for focus in feedback.nextSessionFocus {
    print("🎯 \(focus)")
}
```

## Input

The engine accepts `PerformanceFeatures` containing:
- `issues`: Array of detected performance issues with severity and confidence
- Other performance metrics (trajectories, movement, contacts, rallies)

## Output

The engine returns `CoachingFeedback` containing:
- `insights`: Array of coaching insights with titles and descriptions
- `practiceSuggestions`: Array of practice drills for each issue
- `quickTips`: Array of 2-3 quick tips for immediate improvement
- `nextSessionFocus`: Array of 2-3 focus areas for next session

## Error Handling

The engine throws `CoachingGenerationError` in the following cases:

- **insufficientFeatures**: No performance issues detected
- **templateNotFound**: Sport-specific templates not available (future multi-sport support)

## Multi-Sport Support

Currently implements pickleball-specific templates. The architecture supports adding sport-specific templates for other racket sports (e.g., tennis, padel) by extending the template methods with sport-specific logic.

## Testing

Comprehensive unit tests validate:
- Issue prioritization with impact weights
- Top 5 issue selection
- Plain-language description generation
- Confidence-aware language application
- Practice suggestion mapping
- Quick tip generation
- Next session focus generation
- Error handling for insufficient data

Run tests:
```bash
xcodebuild test -scheme nextmove -only-testing:nextmoveTests/CoachingEngineTests
```

## Implementation Notes

### Severity Scoring

The severity score combines the issue's inherent severity (from feature extraction) with its impact weight:

```swift
weighted_severity = issue.severity × impact_weight[issue.type]
```

This ensures that high-impact issues (like recovery positioning) are prioritized even if their raw severity is lower than other issues.

### Language Qualification

For medium-confidence insights, the engine applies qualifying language by replacing direct statements:

- "You tend to" → "You appear to"
- "You are often" → "You may be"
- "You show" → "You seem to show"

This maintains transparency about confidence levels while still providing useful feedback.

### Template Extensibility

Templates are organized by issue type and sport type, making it easy to add new sports or customize feedback for different skill levels in the future.

## Future Enhancements

Potential improvements for future iterations:

1. **Skill-Level Adaptation**: Adjust language complexity based on player skill level
2. **Progress Tracking**: Compare current issues with historical data to show improvement
3. **Personalization**: Learn player preferences for feedback style
4. **Video Timestamps**: Link insights to specific video moments
5. **Multi-Language Support**: Translate templates to other languages
6. **Custom Drills**: Allow coaches to add custom practice suggestions

## Related Components

- **FeatureExtractor**: Detects performance issues from tracks
- **AnalysisPipeline**: Orchestrates the complete analysis workflow
- **GameAnalysis**: Stores coaching feedback for display in UI
