//
//  ConfigurationManagerTests.swift
//  nextmoveTests
//

import XCTest
@testable import nextmove

class ConfigurationManagerTests: XCTestCase {
    
    func testSharedInstance() {
        let config1 = ConfigurationManager.shared
        let config2 = ConfigurationManager.shared
        
        XCTAssertTrue(config1 === config2, "Should return same instance")
    }
    
    func testDefaultValues() {
        let config = ConfigurationManager.shared
        
        // Should have default base URL
        XCTAssertEqual(config.openAIBaseURL, "https://api.openai.com/v1")
        
        // Should have default model
        XCTAssertEqual(config.openAIModel, "gpt-4o-mini")
    }
    
    func testGetWithDefault() {
        let config = ConfigurationManager.shared
        
        let value = config.get("NONEXISTENT_KEY", default: "default_value")
        XCTAssertEqual(value, "default_value")
    }
}
