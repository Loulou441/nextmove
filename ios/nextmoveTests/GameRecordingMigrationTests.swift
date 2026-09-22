//
//  GameRecordingMigrationTests.swift
//  nextmoveTests
//
//  Tests for GameRecording sportType migration logic
//

import XCTest
@testable import nextmove

final class GameRecordingMigrationTests: XCTestCase {
    
    // Test that new recordings include sportType
    func testNewRecordingIncludesSportType() {
        let recording = GameRecording(
            title: "Test Game",
            videoURL: URL(string: "file:///test.mp4"),
            duration: 120.0,
            sportType: .tennis
        )
        
        XCTAssertEqual(recording.sportType, .tennis)
    }
    
    // Test that recordings default to pickleball when sportType is not specified
    func testRecordingDefaultsToPickleball() {
        let recording = GameRecording(
            title: "Test Game",
            videoURL: URL(string: "file:///test.mp4"),
            duration: 120.0
        )
        
        XCTAssertEqual(recording.sportType, .pickleball)
    }
    
    // Test that legacy recordings without sportType decode to pickleball
    func testLegacyRecordingMigration() throws {
        // Create JSON data representing a legacy recording without sportType
        let legacyJSON = """
        {
            "id": "12345678-1234-1234-1234-123456789012",
            "title": "Legacy Game",
            "date": 694224000.0,
            "duration": 180.0,
            "status": "completed"
        }
        """
        
        let jsonData = legacyJSON.data(using: .utf8)!
        let decoder = JSONDecoder()
        
        let recording = try decoder.decode(GameRecording.self, from: jsonData)
        
        // Legacy recording should default to pickleball
        XCTAssertEqual(recording.sportType, .pickleball)
        XCTAssertEqual(recording.title, "Legacy Game")
        XCTAssertEqual(recording.duration, 180.0)
    }
    
    // Test that recordings with sportType decode correctly
    func testRecordingWithSportTypeDecodes() throws {
        let json = """
        {
            "id": "12345678-1234-1234-1234-123456789012",
            "title": "Tennis Game",
            "date": 694224000.0,
            "duration": 240.0,
            "status": "pending",
            "sportType": "tennis"
        }
        """
        
        let jsonData = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        
        let recording = try decoder.decode(GameRecording.self, from: jsonData)
        
        XCTAssertEqual(recording.sportType, .tennis)
        XCTAssertEqual(recording.title, "Tennis Game")
    }
    
    // Test that sportType is encoded correctly
    func testSportTypeEncoding() throws {
        let recording = GameRecording(
            title: "Test Game",
            videoURL: URL(string: "file:///test.mp4"),
            duration: 120.0,
            sportType: .tennis
        )
        
        let encoder = JSONEncoder()
        let data = try encoder.encode(recording)
        
        let decoder = JSONDecoder()
        let decodedRecording = try decoder.decode(GameRecording.self, from: data)
        
        XCTAssertEqual(decodedRecording.sportType, .tennis)
        XCTAssertEqual(decodedRecording.title, recording.title)
    }
}
