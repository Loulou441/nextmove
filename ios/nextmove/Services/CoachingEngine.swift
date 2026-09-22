//
//  CoachingEngine.swift
//  nextmove
//
//  Translates performance metrics into human-readable coaching feedback
//  Validates: Requirements 8.1-8.10
//

import Foundation

/// CoachingEngine translates PerformanceFeatures into human-readable CoachingFeedback
/// Implements issue prioritization, plain-language generation, and confidence-aware messaging
class CoachingEngine: CoachingEngineProtocol {
    
    // MARK: - Impact Weights
    
    /// Impact weights for severity scoring (higher = more significant)
    /// Validates: Requirement 8.7
    private let impactWeights: [IssueType: Float] = [
        .recoveryPositioning: 1.0,
        .depthPositioning: 0.9,
        .coverageImbalance: 0.8,
        .reactionTiming: 0.7,
        .sideSpecificTiming: 0.7,
        .staticPositioning: 0.6
    ]
    
    // MARK: - Public Methods
    
    /// Generates coaching feedback from performance features
    /// Validates: Requirements 8.1-8.10
    func generateCoaching(from features: PerformanceFeatures, sportType: SportType) async throws -> CoachingFeedback {
        // Validate input
        guard !features.issues.isEmpty else {
            throw CoachingGenerationError.insufficientFeatures
        }
        
        // Sort issues by severity (impact on performance)
        // Validates: Requirement 8.7
        let sortedIssues = sortIssuesBySeverity(features.issues)
        
        // Select top 5 most significant issues
        // Validates: Requirement 8.9
        let topIssues = Array(sortedIssues.prefix(5))
        
        // Generate insights with plain-language descriptions
        // Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.8
        let insights = topIssues.map { issue in
            generateInsight(for: issue, sportType: sportType)
        }
        
        // Generate practice suggestions for each issue
        // Validates: Requirement 8.5
        let practiceSuggestions = topIssues.map { issue in
            generatePracticeSuggestion(for: issue.type)
        }
        
        // Generate quick tips for immediate improvement
        // Validates: Requirement 8.6
        let quickTips = generateQuickTips(for: topIssues, sportType: sportType)
        
        // Generate next session focus recommendations
        // Validates: Requirement 8.10
        let nextSessionFocus = generateNextSessionFocus(for: topIssues)
        
        return CoachingFeedback(
            insights: insights,
            practiceSuggestions: practiceSuggestions,
            quickTips: quickTips,
            nextSessionFocus: nextSessionFocus
        )
    }
    
    // MARK: - Private Methods - Issue Sorting
    
    /// Sorts issues by severity using impact weights
    /// Validates: Requirement 8.7
    private func sortIssuesBySeverity(_ issues: [PerformanceIssue]) -> [PerformanceIssue] {
        return issues.sorted { issue1, issue2 in
            let weight1 = impactWeights[issue1.type] ?? 0.5
            let weight2 = impactWeights[issue2.type] ?? 0.5
            
            // Compute weighted severity
            let severity1 = issue1.severity * weight1
            let severity2 = issue2.severity * weight2
            
            return severity1 > severity2
        }
    }
    
    // MARK: - Private Methods - Insight Generation
    
    /// Generates a coaching insight with plain-language description
    /// Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.8
    private func generateInsight(for issue: PerformanceIssue, sportType: SportType) -> CoachingInsight {
        let title = generateTitle(for: issue.type)
        let description = generateDescription(for: issue, sportType: sportType)
        
        return CoachingInsight(
            title: title,
            description: description,
            severity: issue.severity,
            confidence: issue.confidence
        )
    }
    
    /// Generates a title for an issue type
    private func generateTitle(for issueType: IssueType) -> String {
        switch issueType {
        case .staticPositioning:
            return "Limited Court Movement"
        case .depthPositioning:
            return "Positioning Too Deep"
        case .reactionTiming:
            return "Delayed Reactions"
        case .coverageImbalance:
            return "Unbalanced Court Coverage"
        case .sideSpecificTiming:
            return "Timing Issues on One Side"
        case .recoveryPositioning:
            return "Poor Recovery Position"
        }
    }
    
    /// Generates a plain-language description for an issue
    /// Applies confidence-aware language based on confidence score
    /// Validates: Requirements 8.2, 8.3, 8.4, 8.8
    private func generateDescription(for issue: PerformanceIssue, sportType: SportType) -> String {
        // Get base template for the issue type
        let template = getDescriptionTemplate(for: issue.type, sportType: sportType)
        
        // Apply confidence-aware language
        // Validates: Requirement 8.8
        let qualifiedDescription: String
        if issue.confidence > 0.7 {
            // High confidence: direct statements
            qualifiedDescription = template
        } else if issue.confidence >= 0.6 {
            // Medium confidence: qualifying language
            qualifiedDescription = applyQualifyingLanguage(template)
        } else {
            // Low confidence: exclude from feedback (should not reach here due to filtering)
            qualifiedDescription = template
        }
        
        return qualifiedDescription
    }
    
    /// Gets the description template for an issue type
    /// Validates: Requirements 8.2, 8.3, 8.4
    private func getDescriptionTemplate(for issueType: IssueType, sportType: SportType) -> String {
        // Currently only pickleball templates implemented.
        // Sport-specific templates for other racket sports would be added here.
        
        switch issueType {
        case .staticPositioning:
            return "You tend to stay in the same area for extended periods. Try to stay more mobile and adjust your position based on the ball location."
            
        case .depthPositioning:
            return "You are often positioned too far behind the kitchen line. Move forward after your return to control the net."
            
        case .reactionTiming:
            return "You show delayed movement after your opponent contacts the ball. Work on anticipating shots and reacting more quickly."
            
        case .coverageImbalance:
            return "Your court coverage is stronger on one side than the other. Practice moving to your weaker side to improve balance."
            
        case .sideSpecificTiming:
            return "You are often contacting the ball late on one side. Focus on earlier preparation and weight transfer on that side."
            
        case .recoveryPositioning:
            return "After hitting shots, you tend to stay where you are instead of returning to center. Practice the split-step and recovery to center position."
        }
    }
    
    /// Applies qualifying language for medium-confidence insights
    /// Validates: Requirement 8.8
    private func applyQualifyingLanguage(_ description: String) -> String {
        // Replace direct statements with qualifying language
        let qualifiers = [
            ("You tend to", "You appear to"),
            ("You are often", "You may be"),
            ("You show", "You seem to show"),
            ("Your court coverage is", "Your court coverage appears to be")
        ]
        
        var qualified = description
        for (direct, qualifying) in qualifiers {
            qualified = qualified.replacingOccurrences(of: direct, with: qualifying)
        }
        
        return qualified
    }
    
    // MARK: - Private Methods - Practice Suggestions
    
    /// Generates a practice suggestion for an issue type
    /// Validates: Requirement 8.5
    private func generatePracticeSuggestion(for issueType: IssueType) -> PracticeSuggestion {
        switch issueType {
        case .staticPositioning:
            return PracticeSuggestion(
                issue: issueType,
                drill: "Shadowing Drill",
                description: "Practice moving to different court positions without a ball. Focus on quick, efficient movements and maintaining balance."
            )
            
        case .depthPositioning:
            return PracticeSuggestion(
                issue: issueType,
                drill: "Kitchen Line Drill",
                description: "Practice dinking while maintaining position at the kitchen line. Focus on staying close to the line without stepping into the kitchen."
            )
            
        case .reactionTiming:
            return PracticeSuggestion(
                issue: issueType,
                drill: "Split-Step Drill",
                description: "Practice the split-step timing: small hop as your opponent contacts the ball. This prepares you to move quickly in any direction."
            )
            
        case .coverageImbalance:
            return PracticeSuggestion(
                issue: issueType,
                drill: "Side-to-Side Drill",
                description: "Have a partner hit alternating shots to your weaker side. Focus on moving efficiently and maintaining good form on that side."
            )
            
        case .sideSpecificTiming:
            return PracticeSuggestion(
                issue: issueType,
                drill: "Wall Drill",
                description: "Practice shots on your weaker side against a wall. Focus on early contact point and smooth weight transfer through the shot."
            )
            
        case .recoveryPositioning:
            return PracticeSuggestion(
                issue: issueType,
                drill: "Recovery Drill",
                description: "Hit a shot, then immediately return to center position. Practice this pattern until recovery becomes automatic after every shot."
            )
        }
    }
    
    // MARK: - Private Methods - Quick Tips
    
    /// Generates quick tips for immediate improvement
    /// Validates: Requirement 8.6
    private func generateQuickTips(for issues: [PerformanceIssue], sportType: SportType) -> [String] {
        var tips: [String] = []
        
        // Add issue-specific tips
        for issue in issues.prefix(3) { // Top 3 issues
            if let tip = getQuickTip(for: issue.type) {
                tips.append(tip)
            }
        }
        
        // Add general tips if we have fewer than 3
        if tips.count < 3 {
            tips.append("Stay on your toes and keep moving")
            if tips.count < 3 {
                tips.append("Keep your paddle up and ready")
            }
        }
        
        return Array(tips.prefix(3))
    }
    
    /// Gets a quick tip for an issue type
    private func getQuickTip(for issueType: IssueType) -> String? {
        switch issueType {
        case .staticPositioning:
            return "Stay on your toes and keep moving"
        case .depthPositioning:
            return "Move forward after your return"
        case .reactionTiming:
            return "Split-step when your opponent contacts the ball"
        case .coverageImbalance:
            return "Practice moving to your weaker side"
        case .sideSpecificTiming:
            return "Prepare earlier on your weaker side"
        case .recoveryPositioning:
            return "Recover to center after each shot"
        }
    }
    
    // MARK: - Private Methods - Next Session Focus
    
    /// Generates focus areas for next session
    /// Validates: Requirement 8.10
    private func generateNextSessionFocus(for issues: [PerformanceIssue]) -> [String] {
        var focusAreas: [String] = []
        
        // Take top 2-3 issues for next session focus
        for issue in issues.prefix(3) {
            focusAreas.append(getFocusArea(for: issue.type))
        }
        
        return focusAreas
    }
    
    /// Gets a focus area description for an issue type
    private func getFocusArea(for issueType: IssueType) -> String {
        switch issueType {
        case .staticPositioning:
            return "Work on court mobility and dynamic positioning"
        case .depthPositioning:
            return "Focus on moving forward to control the net"
        case .reactionTiming:
            return "Practice split-step timing and quick reactions"
        case .coverageImbalance:
            return "Improve movement and coverage on your weaker side"
        case .sideSpecificTiming:
            return "Develop earlier contact timing on your weaker side"
        case .recoveryPositioning:
            return "Build automatic recovery to center position"
        }
    }
}
