//
//  CoachingEngineTests.swift
//  nextmoveTests
//
//  Unit tests for CoachingEngine
//  Validates: Requirements 8.1-8.10
//

import XCTest
import AVFoundation
@testable import nextmove

final class CoachingEngineTests: XCTestCase {
    
    var coachingEngine: CoachingEngine!
    
    override func setUp() {
        super.setUp()
        coachingEngine = CoachingEngine()
    }
    
    override func tearDown() {
        coachingEngine = nil
        super.tearDown()
    }
    
    // MARK: - Test Issue Prioritization
    
    /// Test that issues are sorted by severity with impact weights
    /// Validates: Requirement 8.7
    func testIssuePrioritization() async throws {
        // Create issues with different types and severities
        let issues = [
            PerformanceIssue(
                type: .staticPositioning,
                severity: 0.8,
                occurrences: 10,
                description: "Static positioning detected",
                confidence: 0.75
            ),
            PerformanceIssue(
                type: .recoveryPositioning,
                severity: 0.6,
                occurrences: 8,
                description: "Poor recovery detected",
                confidence: 0.8
            ),
            PerformanceIssue(
                type: .depthPositioning,
                severity: 0.7,
                occurrences: 12,
                description: "Depth positioning issue",
                confidence: 0.85
            )
        ]
        
        let features = createMockFeatures(with: issues)
        
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        // Recovery positioning should be first (severity 0.6 * weight 1.0 = 0.6)
        // Depth positioning should be second (severity 0.7 * weight 0.9 = 0.63)
        // Static positioning should be third (severity 0.8 * weight 0.6 = 0.48)
        XCTAssertEqual(feedback.insights.count, 3)
        XCTAssertTrue(feedback.insights[0].title.contains("Recovery"))
        XCTAssertTrue(feedback.insights[1].title.contains("Depth"))
        XCTAssertTrue(feedback.insights[2].title.contains("Movement"))
    }
    
    // MARK: - Test Top 5 Selection
    
    /// Test that only top 5 issues are included in feedback
    /// Validates: Requirement 8.9
    func testTop5IssueSelection() async throws {
        // Create 7 issues
        let issues = (0..<7).map { index in
            PerformanceIssue(
                type: .staticPositioning,
                severity: Float(index) / 10.0,
                occurrences: 5,
                description: "Issue \(index)",
                confidence: 0.75
            )
        }
        
        let features = createMockFeatures(with: issues)
        
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        // Should only have top 5 issues
        XCTAssertEqual(feedback.insights.count, 5)
        XCTAssertEqual(feedback.practiceSuggestions.count, 5)
    }
    
    // MARK: - Test Plain-Language Descriptions
    
    /// Test that plain-language descriptions are generated for each issue type
    /// Validates: Requirements 8.1, 8.2, 8.3, 8.4
    func testPlainLanguageDescriptions() async throws {
        let issueTypes: [IssueType] = [
            .staticPositioning,
            .depthPositioning,
            .reactionTiming,
            .coverageImbalance,
            .sideSpecificTiming,
            .recoveryPositioning
        ]
        
        for issueType in issueTypes {
            let issue = PerformanceIssue(
                type: issueType,
                severity: 0.7,
                occurrences: 5,
                description: "Test issue",
                confidence: 0.8
            )
            
            let features = createMockFeatures(with: [issue])
            
            let feedback = try await coachingEngine.generateCoaching(
                from: features,
                sportType: .pickleball
            )
            
            XCTAssertEqual(feedback.insights.count, 1)
            let insight = feedback.insights[0]
            
            // Verify description is not empty and contains actionable language
            XCTAssertFalse(insight.description.isEmpty)
            XCTAssertGreaterThan(insight.description.count, 20)
        }
    }
    
    // MARK: - Test Confidence-Aware Language
    
    /// Test that high confidence (> 0.7) uses direct statements
    /// Validates: Requirement 8.8
    func testHighConfidenceLanguage() async throws {
        let issue = PerformanceIssue(
            type: .staticPositioning,
            severity: 0.7,
            occurrences: 10,
            description: "Static positioning",
            confidence: 0.85 // High confidence
        )
        
        let features = createMockFeatures(with: [issue])
        
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        let description = feedback.insights[0].description
        
        // Should use direct language
        XCTAssertTrue(
            description.contains("You tend to") ||
            description.contains("You are often") ||
            description.contains("You show")
        )
    }
    
    /// Test that medium confidence (0.6-0.7) uses qualifying language
    /// Validates: Requirement 8.8
    func testMediumConfidenceLanguage() async throws {
        let issue = PerformanceIssue(
            type: .staticPositioning,
            severity: 0.7,
            occurrences: 10,
            description: "Static positioning",
            confidence: 0.65 // Medium confidence
        )
        
        let features = createMockFeatures(with: [issue])
        
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        let description = feedback.insights[0].description
        
        // Should use qualifying language
        XCTAssertTrue(
            description.contains("appear") ||
            description.contains("may be") ||
            description.contains("seem")
        )
    }
    
    // MARK: - Test Practice Suggestions
    
    /// Test that practice suggestions are generated for each issue type
    /// Validates: Requirement 8.5
    func testPracticeSuggestions() async throws {
        let issueTypes: [IssueType] = [
            .staticPositioning,
            .depthPositioning,
            .reactionTiming,
            .coverageImbalance,
            .sideSpecificTiming,
            .recoveryPositioning
        ]
        
        for issueType in issueTypes {
            let issue = PerformanceIssue(
                type: issueType,
                severity: 0.7,
                occurrences: 5,
                description: "Test issue",
                confidence: 0.8
            )
            
            let features = createMockFeatures(with: [issue])
            
            let feedback = try await coachingEngine.generateCoaching(
                from: features,
                sportType: .pickleball
            )
            
            XCTAssertEqual(feedback.practiceSuggestions.count, 1)
            let suggestion = feedback.practiceSuggestions[0]
            
            // Verify suggestion has drill name and description
            XCTAssertFalse(suggestion.drill.isEmpty)
            XCTAssertFalse(suggestion.description.isEmpty)
            XCTAssertEqual(suggestion.issue, issueType)
        }
    }
    
    // MARK: - Test Quick Tips
    
    /// Test that quick tips are generated
    /// Validates: Requirement 8.6
    func testQuickTips() async throws {
        let issues = [
            PerformanceIssue(
                type: .staticPositioning,
                severity: 0.8,
                occurrences: 10,
                description: "Static positioning",
                confidence: 0.75
            ),
            PerformanceIssue(
                type: .depthPositioning,
                severity: 0.7,
                occurrences: 8,
                description: "Depth positioning",
                confidence: 0.8
            )
        ]
        
        let features = createMockFeatures(with: issues)
        
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        // Should have quick tips
        XCTAssertGreaterThanOrEqual(feedback.quickTips.count, 2)
        XCTAssertLessThanOrEqual(feedback.quickTips.count, 3)
        
        // Tips should be concise
        for tip in feedback.quickTips {
            XCTAssertFalse(tip.isEmpty)
            XCTAssertLessThan(tip.count, 100)
        }
    }
    
    // MARK: - Test Next Session Focus
    
    /// Test that next session focus areas are generated
    /// Validates: Requirement 8.10
    func testNextSessionFocus() async throws {
        let issues = [
            PerformanceIssue(
                type: .recoveryPositioning,
                severity: 0.8,
                occurrences: 10,
                description: "Recovery issue",
                confidence: 0.75
            ),
            PerformanceIssue(
                type: .depthPositioning,
                severity: 0.7,
                occurrences: 8,
                description: "Depth issue",
                confidence: 0.8
            )
        ]
        
        let features = createMockFeatures(with: issues)
        
        let feedback = try await coachingEngine.generateCoaching(
            from: features,
            sportType: .pickleball
        )
        
        // Should have focus areas
        XCTAssertGreaterThanOrEqual(feedback.nextSessionFocus.count, 2)
        XCTAssertLessThanOrEqual(feedback.nextSessionFocus.count, 3)
        
        // Focus areas should be actionable
        for focus in feedback.nextSessionFocus {
            XCTAssertFalse(focus.isEmpty)
            XCTAssertGreaterThan(focus.count, 10)
        }
    }
    
    // MARK: - Test Error Handling
    
    /// Test that error is thrown when no issues are provided
    func testInsufficientFeaturesError() async {
        let features = createMockFeatures(with: [])
        
        do {
            _ = try await coachingEngine.generateCoaching(
                from: features,
                sportType: .pickleball
            )
            XCTFail("Should have thrown CoachingGenerationError.insufficientFeatures")
        } catch CoachingGenerationError.insufficientFeatures {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
    
    // MARK: - Helper Methods
    
    /// Creates mock PerformanceFeatures with specified issues
    private func createMockFeatures(with issues: [PerformanceIssue]) -> PerformanceFeatures {
        let mockCoverage = CourtCoverage(
            zones: [:],
            leftRightBalance: 0.0,
            kitchenLineProximity: 0.5,
            baselineProximity: 0.5
        )
        
        let mockMovement = PlayerMovement(
            courtCoverage: mockCoverage,
            movementSpeed: [],
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
