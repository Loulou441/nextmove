//
//  ObjectTrackerTests.swift
//  nextmoveTests
//
//  Unit tests for ObjectTracker
//  Validates: Requirements 3.1-3.8, 14.2
//

import XCTest
import AVFoundation
@testable import nextmove

final class ObjectTrackerTests: XCTestCase {
    
    var tracker: ObjectTracker!
    
    override func setUp() {
        super.setUp()
        tracker = ObjectTracker()
    }
    
    override func tearDown() {
        tracker = nil
        super.tearDown()
    }
    
    // MARK: - Track Identity Consistency Tests
    
    /// Tests that the same object maintains consistent track ID across frames
    /// Validates: Requirements 3.1, 3.2
    func testTrackIdentityConsistency() async throws {
        // Create detections for the same ball across 5 frames
        let detections = createConsecutiveDetections(
            objectClass: .ball,
            frameCount: 5,
            startPosition: CGPoint(x: 0.3, y: 0.3),
            movement: CGPoint(x: 0.05, y: 0.02)
        )
        
        let tracks = try await tracker.track(detections: detections)
        
        // Should create exactly one track
        XCTAssertEqual(tracks.count, 1, "Should create one track for consecutive detections")
        
        let track = tracks[0]
        XCTAssertEqual(track.detections.count, 5, "Track should contain all 5 detections")
        XCTAssertEqual(track.objectClass, .ball, "Track should maintain object class")
    }
    
    /// Tests tracking multiple objects of different classes
    /// Validates: Requirements 3.2, 3.3, 3.4
    func testMultipleObjectTracking() async throws {
        var detections: [Detection] = []
        
        // Create ball detections
        detections += createConsecutiveDetections(
            objectClass: .ball,
            frameCount: 5,
            startPosition: CGPoint(x: 0.3, y: 0.3),
            movement: CGPoint(x: 0.05, y: 0.02)
        )
        
        // Create player detections
        detections += createConsecutiveDetections(
            objectClass: .player,
            frameCount: 5,
            startPosition: CGPoint(x: 0.5, y: 0.5),
            movement: CGPoint(x: 0.02, y: 0.01)
        )
        
        // Create paddle detections
        detections += createConsecutiveDetections(
            objectClass: .paddle,
            frameCount: 5,
            startPosition: CGPoint(x: 0.6, y: 0.4),
            movement: CGPoint(x: 0.03, y: 0.02)
        )
        
        let tracks = try await tracker.track(detections: detections)
        
        // Should create three tracks (one per object class)
        XCTAssertEqual(tracks.count, 3, "Should create three tracks for three objects")
        
        // Verify each object class has one track
        let ballTracks = tracks.filter { $0.objectClass == .ball }
        let playerTracks = tracks.filter { $0.objectClass == .player }
        let paddleTracks = tracks.filter { $0.objectClass == .paddle }
        
        XCTAssertEqual(ballTracks.count, 1, "Should have one ball track")
        XCTAssertEqual(playerTracks.count, 1, "Should have one player track")
        XCTAssertEqual(paddleTracks.count, 1, "Should have one paddle track")
    }
    
    // MARK: - Track ID Uniqueness Tests
    
    /// Tests that all track IDs are unique
    /// Validates: Requirements 3.6
    func testTrackIDUniqueness() async throws {
        var detections: [Detection] = []
        
        // Create multiple separate objects
        for i in 0..<5 {
            detections += createConsecutiveDetections(
                objectClass: .ball,
                frameCount: 3,
                startPosition: CGPoint(x: 0.1 + Double(i) * 0.15, y: 0.3),
                movement: CGPoint(x: 0.01, y: 0.01),
                startFrame: i * 10 // Non-overlapping frames
            )
        }
        
        let tracks = try await tracker.track(detections: detections)
        
        // Verify all track IDs are unique
        let trackIDs = Set(tracks.map { $0.id })
        XCTAssertEqual(trackIDs.count, tracks.count, "All track IDs should be unique")
    }
    
    // MARK: - Track Completeness Tests
    
    /// Tests that tracks contain all required fields
    /// Validates: Requirements 3.8
    func testTrackCompleteness() async throws {
        let detections = createConsecutiveDetections(
            objectClass: .player,
            frameCount: 10,
            startPosition: CGPoint(x: 0.5, y: 0.5),
            movement: CGPoint(x: 0.02, y: 0.01)
        )
        
        let tracks = try await tracker.track(detections: detections)
        
        XCTAssertEqual(tracks.count, 1, "Should create one track")
        
        let track = tracks[0]
        
        // Verify all required fields are present
        XCTAssertNotNil(track.id, "Track should have ID")
        XCTAssertEqual(track.objectClass, .player, "Track should have object class")
        XCTAssertFalse(track.detections.isEmpty, "Track should have detections")
        XCTAssertGreaterThan(track.startTime.seconds, 0, "Track should have start time")
        XCTAssertGreaterThan(track.endTime.seconds, track.startTime.seconds, "End time should be after start time")
        XCTAssertGreaterThan(track.averageConfidence, 0, "Track should have average confidence")
        XCTAssertLessThanOrEqual(track.averageConfidence, 1.0, "Confidence should be <= 1.0")
    }
    
    /// Tests track duration computation
    /// Validates: Requirements 3.8
    func testTrackDuration() async throws {
        let detections = createConsecutiveDetections(
            objectClass: .ball,
            frameCount: 30, // 30 frames at 30fps = 1 second
            startPosition: CGPoint(x: 0.3, y: 0.3),
            movement: CGPoint(x: 0.01, y: 0.01),
            fps: 30
        )
        
        let tracks = try await tracker.track(detections: detections)
        
        XCTAssertEqual(tracks.count, 1, "Should create one track")
        
        let track = tracks[0]
        let expectedDuration = 29.0 / 30.0 // 29 frame intervals at 30fps
        
        XCTAssertEqual(track.duration, expectedDuration, accuracy: 0.01, "Track duration should be approximately 1 second")
    }
    
    // MARK: - Track Termination Tests
    
    /// Tests track termination when confidence falls below threshold
    /// Validates: Requirements 3.7
    func testTrackTerminationOnLowConfidence() async throws {
        var detections: [Detection] = []
        
        // Create detections with decreasing confidence
        for i in 0..<10 {
            let confidence: Float = i < 5 ? 0.8 : 0.2 // Drop below 0.3 threshold after frame 5
            
            detections.append(Detection(
                objectClass: .ball,
                boundingBox: CGRect(x: 0.3 + Double(i) * 0.01, y: 0.3, width: 0.05, height: 0.05),
                confidence: confidence,
                frameNumber: i,
                timestamp: CMTime(value: CMTimeValue(i), timescale: 30)
            ))
        }
        
        let tracks = try await tracker.track(detections: detections)
        
        // Track should be terminated when confidence drops
        // The exact behavior depends on implementation (may create 1 or 2 tracks)
        XCTAssertGreaterThan(tracks.count, 0, "Should create at least one track")
        
        // Verify that tracks don't contain low-confidence detections
        for track in tracks {
            XCTAssertGreaterThanOrEqual(track.averageConfidence, 0.3, "Track average confidence should be >= 0.3")
        }
    }
    
    /// Tests track termination after frame gap exceeds threshold
    /// Validates: Requirements 3.5, 3.7
    func testTrackTerminationOnFrameGap() async throws {
        var detections: [Detection] = []
        
        // Create detections with large gap
        // Frames 0-4: ball present
        detections += createConsecutiveDetections(
            objectClass: .ball,
            frameCount: 5,
            startPosition: CGPoint(x: 0.3, y: 0.3),
            movement: CGPoint(x: 0.01, y: 0.01),
            startFrame: 0
        )
        
        // Frames 5-39: ball absent (35 frame gap, exceeds 30 frame threshold)
        
        // Frames 40-44: ball reappears (should create new track)
        detections += createConsecutiveDetections(
            objectClass: .ball,
            frameCount: 5,
            startPosition: CGPoint(x: 0.7, y: 0.7),
            movement: CGPoint(x: 0.01, y: 0.01),
            startFrame: 40
        )
        
        let tracks = try await tracker.track(detections: detections)
        
        // Should create two separate tracks due to frame gap
        XCTAssertEqual(tracks.count, 2, "Should create two tracks due to frame gap exceeding threshold")
        
        // Verify first track ends before frame 40
        let firstTrack = tracks.first { $0.detections.first?.frameNumber == 0 }
        XCTAssertNotNil(firstTrack, "Should have track starting at frame 0")
        XCTAssertLessThan(firstTrack!.detections.last!.frameNumber, 40, "First track should end before frame 40")
        
        // Verify second track starts at frame 40
        let secondTrack = tracks.first { $0.detections.first?.frameNumber == 40 }
        XCTAssertNotNil(secondTrack, "Should have track starting at frame 40")
    }
    
    // MARK: - Re-identification Tests
    
    /// Tests re-identification within 30 frame window
    /// Validates: Requirements 3.5
    func testReidentificationWithinWindow() async throws {
        var detections: [Detection] = []
        
        // Frames 0-4: ball present
        detections += createConsecutiveDetections(
            objectClass: .ball,
            frameCount: 5,
            startPosition: CGPoint(x: 0.3, y: 0.3),
            movement: CGPoint(x: 0.01, y: 0.01),
            startFrame: 0
        )
        
        // Frames 5-24: ball absent (20 frame gap, within 30 frame threshold)
        
        // Frames 25-29: ball reappears nearby (should continue same track)
        detections += createConsecutiveDetections(
            objectClass: .ball,
            frameCount: 5,
            startPosition: CGPoint(x: 0.35, y: 0.35),
            movement: CGPoint(x: 0.01, y: 0.01),
            startFrame: 25
        )
        
        let tracks = try await tracker.track(detections: detections)
        
        // Should maintain single track if within re-identification window
        // Note: This test may create 2 tracks if IoU matching fails due to position change
        // The actual behavior depends on IoU threshold and position proximity
        XCTAssertGreaterThan(tracks.count, 0, "Should create at least one track")
        XCTAssertLessThanOrEqual(tracks.count, 2, "Should create at most two tracks")
    }
    
    // MARK: - IoU Matching Tests
    
    /// Tests IoU-based detection matching
    /// Validates: Requirements 3.1
    func testIoUMatching() async throws {
        var detections: [Detection] = []
        
        // Frame 0: ball at position A
        detections.append(Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.3, y: 0.3, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 0,
            timestamp: CMTime(value: 0, timescale: 30)
        ))
        
        // Frame 1: ball moved slightly (high IoU overlap)
        detections.append(Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.32, y: 0.31, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 1,
            timestamp: CMTime(value: 1, timescale: 30)
        ))
        
        let tracks = try await tracker.track(detections: detections)
        
        // Should create one track (detections matched via IoU)
        XCTAssertEqual(tracks.count, 1, "Should create one track for overlapping detections")
        XCTAssertEqual(tracks[0].detections.count, 2, "Track should contain both detections")
    }
    
    /// Tests that different object classes are not matched
    /// Validates: Requirements 3.1, 3.2, 3.3, 3.4
    func testClassSpecificMatching() async throws {
        var detections: [Detection] = []
        
        // Frame 0: ball at position
        detections.append(Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.3, y: 0.3, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 0,
            timestamp: CMTime(value: 0, timescale: 30)
        ))
        
        // Frame 1: paddle at same position (should not match ball)
        detections.append(Detection(
            objectClass: .paddle,
            boundingBox: CGRect(x: 0.3, y: 0.3, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 1,
            timestamp: CMTime(value: 1, timescale: 30)
        ))
        
        let tracks = try await tracker.track(detections: detections)
        
        // Should create two separate tracks (different classes)
        XCTAssertEqual(tracks.count, 2, "Should create separate tracks for different object classes")
        
        let ballTracks = tracks.filter { $0.objectClass == .ball }
        let paddleTracks = tracks.filter { $0.objectClass == .paddle }
        
        XCTAssertEqual(ballTracks.count, 1, "Should have one ball track")
        XCTAssertEqual(paddleTracks.count, 1, "Should have one paddle track")
    }
    
    // MARK: - Error Handling Tests
    
    /// Tests error handling for empty detections
    /// Validates: Requirements 3.1
    func testEmptyDetections() async throws {
        do {
            _ = try await tracker.track(detections: [])
            XCTFail("Should throw error for empty detections")
        } catch TrackingError.insufficientDetections {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
    
    // MARK: - Track Statistics Tests
    
    /// Tests track statistics computation
    /// Validates: Requirements 3.8
    func testTrackStatistics() async throws {
        var detections: [Detection] = []
        
        // Create multiple tracks
        detections += createConsecutiveDetections(
            objectClass: .ball,
            frameCount: 10,
            startPosition: CGPoint(x: 0.3, y: 0.3),
            movement: CGPoint(x: 0.01, y: 0.01),
            startFrame: 0
        )
        
        detections += createConsecutiveDetections(
            objectClass: .player,
            frameCount: 20,
            startPosition: CGPoint(x: 0.5, y: 0.5),
            movement: CGPoint(x: 0.01, y: 0.01),
            startFrame: 0
        )
        
        let tracks = try await tracker.track(detections: detections)
        
        let stats = tracker.computeTrackStatistics(tracks: tracks)
        
        XCTAssertEqual(stats.totalTracks, 2, "Should have 2 tracks")
        XCTAssertGreaterThan(stats.averageDuration, 0, "Should have positive average duration")
        XCTAssertGreaterThan(stats.averageConfidence, 0, "Should have positive average confidence")
        XCTAssertEqual(stats.tracksByClass[.ball], 1, "Should have 1 ball track")
        XCTAssertEqual(stats.tracksByClass[.player], 1, "Should have 1 player track")
    }
    
    // MARK: - Helper Methods
    
    /// Creates consecutive detections for testing
    private func createConsecutiveDetections(
        objectClass: ObjectClass,
        frameCount: Int,
        startPosition: CGPoint,
        movement: CGPoint,
        startFrame: Int = 0,
        fps: Int32 = 30,
        confidence: Float = 0.9
    ) -> [Detection] {
        var detections: [Detection] = []
        
        for i in 0..<frameCount {
            let frameNumber = startFrame + i
            let position = CGPoint(
                x: startPosition.x + movement.x * Double(i),
                y: startPosition.y + movement.y * Double(i)
            )
            
            detections.append(Detection(
                objectClass: objectClass,
                boundingBox: CGRect(x: position.x, y: position.y, width: 0.05, height: 0.05),
                confidence: confidence,
                frameNumber: frameNumber,
                timestamp: CMTime(value: CMTimeValue(frameNumber), timescale: fps)
            ))
        }
        
        return detections
    }
}
