//
//  LLMServiceTests.swift
//  nextmoveTests
//

import XCTest
@testable import nextmove

class LLMServiceTests: XCTestCase {
    
    func testConfigurationLoading() {
        let config = ConfigurationManager.shared
        
        // Should not crash even without .env file
        XCTAssertNotNil(config.openAIBaseURL)
        XCTAssertNotNil(config.openAIModel)
    }
    
    func testLLMServiceInitialization() {
        let service = LLMService()
        XCTAssertNotNil(service)
    }
    
    func testEnhancedCoachingEngineWithoutAPIKey() async throws {
        // Should fall back to base engine gracefully
        let engine = EnhancedCoachingEngine(useLLM: false)
        
        let features = PerformanceFeatures(
            issues: [
                PerformanceIssue(
                    type: .staticPositioning,
                    severity: 0.8,
                    occurrences: 5,
                    description: "Player tends to stay in same area",
                    confidence: 0.9
                )
            ]
        )
        
        let feedback = try await engine.generateCoaching(from: features, sportType: .pickleball)
        
        XCTAssertFalse(feedback.insights.isEmpty)
        XCTAssertFalse(feedback.practiceSuggestions.isEmpty)
    }
}
