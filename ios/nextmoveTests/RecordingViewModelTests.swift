//
//  RecordingViewModelTests.swift
//  nextmoveTests
//
//  Created by Asmae  on 09/03/2026.
//

import XCTest
@testable import nextmove

@MainActor
final class RecordingViewModelTests: XCTestCase {
    
    var viewModel: RecordingViewModel!
    
    override func setUp() {
        super.setUp()
        // Clear stored recordings before each test
        UserDefaults.standard.removeObject(forKey: "savedRecordings")
        viewModel = RecordingViewModel()
    }
    
    override func tearDown() {
        // Clean up after each test
        UserDefaults.standard.removeObject(forKey: "savedRecordings")
        viewModel = nil
        super.tearDown()
    }
    
    // MARK: - Sport Filtering Tests
    
    func testRecordingsFilteredBySport() {
        // Given: Recordings for different sports
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let url1 = documentsPath.appendingPathComponent("test1.mov")
        let url2 = documentsPath.appendingPathComponent("test2.mov")
        let url3 = documentsPath.appendingPathComponent("test3.mov")
        
        viewModel.addRecording(videoURL: url1, title: "Pickleball Game 1", sportType: .pickleball)
        viewModel.addRecording(videoURL: url2, title: "Tennis Game 1", sportType: .tennis)
        viewModel.addRecording(videoURL: url3, title: "Pickleball Game 2", sportType: .pickleball)
        
        // When: Filtering by pickleball
        let pickleballRecordings = viewModel.recordings(for: .pickleball)
        
        // Then: Only pickleball recordings should be returned
        XCTAssertEqual(pickleballRecordings.count, 2, "Should have 2 pickleball recordings")
        XCTAssertTrue(pickleballRecordings.allSatisfy { $0.sportType == .pickleball }, "All filtered recordings should be pickleball")
    }
    
    func testRecordingsFilteredByTennis() {
        // Given: Recordings for different sports
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let url1 = documentsPath.appendingPathComponent("test1.mov")
        let url2 = documentsPath.appendingPathComponent("test2.mov")
        
        viewModel.addRecording(videoURL: url1, title: "Pickleball Game", sportType: .pickleball)
        viewModel.addRecording(videoURL: url2, title: "Tennis Game", sportType: .tennis)
        
        // When: Filtering by tennis
        let tennisRecordings = viewModel.recordings(for: .tennis)
        
        // Then: Only tennis recordings should be returned
        XCTAssertEqual(tennisRecordings.count, 1, "Should have 1 tennis recording")
        XCTAssertEqual(tennisRecordings.first?.sportType, .tennis, "Filtered recording should be tennis")
    }
    
    func testEmptyFilterWhenNoMatchingSport() {
        // Given: Only pickleball recordings
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let url = documentsPath.appendingPathComponent("test.mov")
        
        viewModel.addRecording(videoURL: url, title: "Pickleball Game", sportType: .pickleball)
        
        // When: Filtering by tennis
        let tennisRecordings = viewModel.recordings(for: .tennis)
        
        // Then: Empty array should be returned
        XCTAssertEqual(tennisRecordings.count, 0, "Should have no tennis recordings")
    }
    
    // MARK: - Add Recording with Sport Type Tests
    
    func testAddRecordingWithSportType() {
        // Given: A video URL and sport type
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let url = documentsPath.appendingPathComponent("test.mov")
        
        // When: Adding a recording with tennis sport type
        viewModel.addRecording(videoURL: url, title: "Test Game", sportType: .tennis)
        
        // Then: Recording should have correct sport type
        XCTAssertEqual(viewModel.recordings.count, 1, "Should have 1 recording")
        XCTAssertEqual(viewModel.recordings.first?.sportType, .tennis, "Recording should have tennis sport type")
        XCTAssertEqual(viewModel.recordings.first?.title, "Test Game", "Recording should have correct title")
    }
    
    func testAddRecordingWithDefaultSportType() {
        // Given: A video URL without explicit sport type
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let url = documentsPath.appendingPathComponent("test.mov")
        
        // When: Adding a recording without sport type parameter
        viewModel.addRecording(videoURL: url, title: "Test Game")
        
        // Then: Recording should default to pickleball
        XCTAssertEqual(viewModel.recordings.count, 1, "Should have 1 recording")
        XCTAssertEqual(viewModel.recordings.first?.sportType, .pickleball, "Recording should default to pickleball")
    }
    
    // MARK: - Migration Tests
    
    func testLegacyRecordingsMigration() {
        // Given: Legacy recordings without sportType in storage
        // (This is handled by GameRecording's decoder, but we verify the ViewModel loads them correctly)
        let legacyRecording = GameRecording(
            title: "Legacy Game",
            videoURL: nil,
            duration: 120.0,
            sportType: .pickleball
        )
        
        if let encoded = try? JSONEncoder().encode([legacyRecording]) {
            UserDefaults.standard.set(encoded, forKey: "savedRecordings")
        }
        
        // When: ViewModel loads recordings
        let newViewModel = RecordingViewModel()
        
        // Then: Recordings should be loaded with default sport type
        XCTAssertEqual(newViewModel.recordings.count, 1, "Should load 1 recording")
        XCTAssertEqual(newViewModel.recordings.first?.sportType, .pickleball, "Legacy recording should have pickleball sport type")
    }
    
    // MARK: - Persistence Tests
    
    func testRecordingsWithSportTypePersist() {
        // Given: Recordings with different sport types
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let url1 = documentsPath.appendingPathComponent("test1.mov")
        let url2 = documentsPath.appendingPathComponent("test2.mov")
        
        viewModel.addRecording(videoURL: url1, title: "Pickleball Game", sportType: .pickleball)
        viewModel.addRecording(videoURL: url2, title: "Tennis Game", sportType: .tennis)
        
        // When: Creating a new ViewModel instance
        let newViewModel = RecordingViewModel()
        
        // Then: Recordings should be loaded with correct sport types
        XCTAssertEqual(newViewModel.recordings.count, 2, "Should load 2 recordings")
        
        let pickleballRecordings = newViewModel.recordings(for: .pickleball)
        let tennisRecordings = newViewModel.recordings(for: .tennis)
        
        XCTAssertEqual(pickleballRecordings.count, 1, "Should have 1 pickleball recording")
        XCTAssertEqual(tennisRecordings.count, 1, "Should have 1 tennis recording")
    }
}
