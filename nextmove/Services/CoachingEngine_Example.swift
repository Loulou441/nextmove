//
//  CoachingEngine_Example.swift
//  nextmove
//
//  Example usage of CoachingEngine
//

import Foundation
import AVFoundation

/// Example demonstrating how to use CoachingEngine to generate coaching feedback
class CoachingEngineExample {
    
    /// Example: Generate coaching feedback from performance features
    func generateFeedbackExample() async throws {
        // Create a CoachingEngine instance
        let coachingEngine = CoachingEngine()
        
        // Create sample performance issues (normally from FeatureExtractor)
        let issues = [
            PerformanceIssue(
                type: .recoveryPositioning,
                severity: 0.8,
                occurrences: 12,
                description: "Player fails to return to center after shots",
                confidence: 0.85
            ),
            PerformanceIssue(
                type: .depthPositioning,
                severity: 0.7,
                occurrences: 15,
                description: "Player positioned too far from kitchen line",
                confidence: 0.75
            ),
            PerformanceIssue(
                type: .coverageImbalance,
                severity: 0.6,
                occurrences: 8,
                description: "Stronger coverage on left side",
                confidence: 0.7
            ),
            PerformanceIssue(
                type: .sideSpecificTiming,
                severity: 0.65,
                occurrences: 10,
                description: "Late contact on backhand side",
                confidence: 0.68
            ),
            PerformanceIssue(
                type: .staticPositioning,
                severity: 0.5,
                occurrences: 6,
                description: "Limited movement in mid-court zone",
                confidence: 0.72
            )
        ]
        
        // Create mock performance features
        let features = createMockPerformanceFeatures(with: issues)
        
        // Generate coaching feedback
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        // Display insights
        print("=== Coaching Insights ===")
        for (index, insight) in feedback.insights.enumerated() {
            print("\n\(index + 1). \(insight.title)")
            print("   Severity: \(String(format: "%.1f", insight.severity * 100))%")
            print("   Confidence: \(String(format: "%.1f", insight.confidence * 100))%")
            print("   \(insight.description)")
        }
        
        // Display practice suggestions
        print("\n\n=== Practice Suggestions ===")
        for (index, suggestion) in feedback.practiceSuggestions.enumerated() {
            print("\n\(index + 1). \(suggestion.drill)")
            print("   \(suggestion.description)")
        }
        
        // Display quick tips
        print("\n\n=== Quick Tips ===")
        for (index, tip) in feedback.quickTips.enumerated() {
            print("\(index + 1). 💡 \(tip)")
        }
        
        // Display next session focus
        print("\n\n=== Next Session Focus ===")
        for (index, focus) in feedback.nextSessionFocus.enumerated() {
            print("\(index + 1). 🎯 \(focus)")
        }
    }
    
    /// Example: High confidence feedback (direct language)
    func highConfidenceFeedbackExample() async throws {
        let coachingEngine = CoachingEngine()
        
        let issue = PerformanceIssue(
            type: .depthPositioning,
            severity: 0.8,
            occurrences: 20,
            description: "Consistently positioned too deep",
            confidence: 0.9 // High confidence
        )
        
        let features = createMockPerformanceFeatures(with: [issue])
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        print("High Confidence Feedback:")
        print(feedback.insights[0].description)
        // Output: "You are often positioned too far behind the kitchen line..."
    }
    
    /// Example: Medium confidence feedback (qualifying language)
    func mediumConfidenceFeedbackExample() async throws {
        let coachingEngine = CoachingEngine()
        
        let issue = PerformanceIssue(
            type: .depthPositioning,
            severity: 0.7,
            occurrences: 8,
            description: "Possibly positioned too deep",
            confidence: 0.65 // Medium confidence
        )
        
        let features = createMockPerformanceFeatures(with: [issue])
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        print("Medium Confidence Feedback:")
        print(feedback.insights[0].description)
        // Output: "You may be positioned too far behind the kitchen line..."
    }
    
    /// Example: Issue prioritization by impact
    func issuePrioritizationExample() async throws {
        let coachingEngine = CoachingEngine()
        
        // Create issues with different impact weights
        let issues = [
            // Static positioning: severity 0.9, weight 0.6 = 0.54
            PerformanceIssue(
                type: .staticPositioning,
                severity: 0.9,
                occurrences: 10,
                description: "Limited movement",
                confidence: 0.8
            ),
            // Recovery positioning: severity 0.6, weight 1.0 = 0.60
            PerformanceIssue(
                type: .recoveryPositioning,
                severity: 0.6,
                occurrences: 8,
                description: "Poor recovery",
                confidence: 0.75
            )
        ]
        
        let features = createMockPerformanceFeatures(with: issues)
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        print("Issue Prioritization:")
        print("1st: \(feedback.insights[0].title) (Recovery - higher impact)")
        print("2nd: \(feedback.insights[1].title) (Static - lower impact)")
        // Recovery positioning appears first despite lower severity
        // because it has higher impact weight (1.0 vs 0.6)
    }
    
    // MARK: - Helper Methods
    
    /// Creates mock performance features for examples
    private func createMockPerformanceFeatures(with issues: [PerformanceIssue]) -> PerformanceFeatures {
        let mockCoverage = CourtCoverage(
            zones: [
                .frontLeft: 0.1,
                .frontCenter: 0.15,
                .frontRight: 0.1,
                .midLeft: 0.15,
                .midCenter: 0.2,
                .midRight: 0.15,
                .backLeft: 0.05,
                .backCenter: 0.05,
                .backRight: 0.05
            ],
            leftRightBalance: -0.2, // Slightly left-biased
            kitchenLineProximity: 0.6,
            baselineProximity: 0.4
        )
        
        let mockMovement = PlayerMovement(
            courtCoverage: mockCoverage,
            movementSpeed: [1.2, 1.5, 1.8, 1.3, 1.6],
            positioningHistory: [],
            recoveryPositions: [],
            confidence: 0.8
        )
        
        return PerformanceFeatures(
            ballTrajectories: [],
            playerMovement: mockMovement,
            contactPoints: [],
            rallies: [],
            issues: issues,
            confidence: 0.8
        )
    }
}

// MARK: - Example Output

/*
 Running generateFeedbackExample() produces output like:
 
 === Coaching Insights ===
 
 1. Poor Recovery Position
    Severity: 80.0%
    Confidence: 85.0%
    After hitting shots, you tend to stay where you are instead of returning to center. Practice the split-step and recovery to center position.
 
 2. Positioning Too Deep
    Severity: 70.0%
    Confidence: 75.0%
    You are often positioned too far behind the kitchen line. Move forward after your return to control the net.
 
 3. Timing Issues on One Side
    Severity: 65.0%
    Confidence: 68.0%
    You may be contacting the ball late on one side. Focus on earlier preparation and weight transfer on that side.
 
 4. Unbalanced Court Coverage
    Severity: 60.0%
    Confidence: 70.0%
    Your court coverage appears to be stronger on one side than the other. Practice moving to your weaker side to improve balance.
 
 5. Limited Court Movement
    Severity: 50.0%
    Confidence: 72.0%
    You appear to stay in the same area for extended periods. Try to stay more mobile and adjust your position based on the ball location.
 
 
 === Practice Suggestions ===
 
 1. Recovery Drill
    Hit a shot, then immediately return to center position. Practice this pattern until recovery becomes automatic after every shot.
 
 2. Kitchen Line Drill
    Practice dinking while maintaining position at the kitchen line. Focus on staying close to the line without stepping into the kitchen.
 
 3. Wall Drill
    Practice shots on your weaker side against a wall. Focus on early contact point and smooth weight transfer through the shot.
 
 4. Side-to-Side Drill
    Have a partner hit alternating shots to your weaker side. Focus on moving efficiently and maintaining good form on that side.
 
 5. Shadowing Drill
    Practice moving to different court positions without a ball. Focus on quick, efficient movements and maintaining balance.
 
 
 === Quick Tips ===
 1. 💡 Recover to center after each shot
 2. 💡 Move forward after your return
 3. 💡 Prepare earlier on your weaker side
 
 
 === Next Session Focus ===
 1. 🎯 Build automatic recovery to center position
 2. 🎯 Focus on moving forward to control the net
 3. 🎯 Develop earlier contact timing on your weaker side
 */
