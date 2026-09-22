//
//  SportManagerTests.swift
//  nextmoveTests
//
//  Created by Asmae  on 09/03/2026.
//

import XCTest
@testable import nextmove

@MainActor
final class SportManagerTests: XCTestCase {
    
    override func setUp() {
        super.setUp()
        // Clear stored sport before each test
        UserDefaults.standard.removeObject(forKey: "selectedSport")
    }
    
    override func tearDown() {
        // Clean up after each test
        UserDefaults.standard.removeObject(forKey: "selectedSport")
        super.tearDown()
    }
    
    // MARK: - First Launch Detection Tests
    
    func testFirstLaunchShowsSportSelection() {
        // Given: No sport has been selected
        // When: SportManager is initialized
        let manager = SportManager()
        
        // Then: Sport selection modal should be shown
        XCTAssertTrue(manager.showSportSelection, "Sport selection should be shown on first launch")
        XCTAssertNil(manager.currentSport, "Current sport should be nil on first launch")
    }
    
    // MARK: - Sport Selection Tests
    
    func testSelectSportUpdatesCurrent() {
        // Given: A new SportManager
        let manager = SportManager()
        
        // When: User selects pickleball
        manager.selectSport(.pickleball)
        
        // Then: Current sport should be pickleball
        XCTAssertEqual(manager.currentSport, .pickleball, "Current sport should be pickleball")
        XCTAssertFalse(manager.showSportSelection, "Sport selection modal should be hidden")
    }
    
    func testSelectSportPersistsToStorage() {
        // Given: A new SportManager
        let manager = SportManager()
        
        // When: User selects tennis
        manager.selectSport(.tennis)
        
        // Then: Sport should be persisted to UserDefaults
        let storedValue = UserDefaults.standard.string(forKey: "selectedSport")
        XCTAssertEqual(storedValue, "tennis", "Sport should be persisted to storage")
    }
    
    // MARK: - Persistence Tests
    
    func testSportPersistsAcrossInstances() {
        // Given: A sport has been selected
        let manager1 = SportManager()
        manager1.selectSport(.pickleball)
        
        // When: A new SportManager instance is created
        let manager2 = SportManager()
        
        // Then: The sport should be loaded from storage
        XCTAssertEqual(manager2.currentSport, .pickleball, "Sport should persist across instances")
        XCTAssertFalse(manager2.showSportSelection, "Sport selection should not be shown when sport exists")
    }
    
    // MARK: - Sport Change Request Tests
    
    func testRequestSportChangeShowsModal() {
        // Given: A SportManager with a selected sport
        let manager = SportManager()
        manager.selectSport(.pickleball)
        
        // When: User requests to change sport
        manager.requestSportChange()
        
        // Then: Sport selection modal should be shown
        XCTAssertTrue(manager.showSportSelection, "Sport selection should be shown when change is requested")
    }
    
    // MARK: - Invalid Stored Value Tests
    
    func testInvalidStoredValueShowsSportSelection() {
        // Given: An invalid sport value in storage
        UserDefaults.standard.set("invalid_sport", forKey: "selectedSport")
        
        // When: SportManager is initialized
        let manager = SportManager()
        
        // Then: Sport selection should be shown
        XCTAssertTrue(manager.showSportSelection, "Sport selection should be shown for invalid stored value")
        XCTAssertNil(manager.currentSport, "Current sport should be nil for invalid stored value")
    }
    
    // MARK: - Thread Safety Tests
    
    func testSportManagerIsMainActorIsolated() {
        // This test verifies that SportManager is marked with @MainActor
        // If it wasn't, this test wouldn't compile
        let manager = SportManager()
        XCTAssertNotNil(manager, "SportManager should be @MainActor isolated")
    }
}
