//
//  ObjectTracker_Example.swift
//  nextmove
//
//  Example usage of ObjectTracker with ObjectDetector
//  This file demonstrates the integration between detection and tracking
//

import Foundation
import AVFoundation

/// Example: Tracking objects across video frames
/// This demonstrates the typical workflow for object tracking in the analysis pipeline
func exampleObjectTracking() async throws {
    // MARK: - Setup
    
    // Initialize components
    let modelManager = ModelManager()
    let objectDetector = ObjectDetector(modelManager: modelManager)
    let objectTracker = ObjectTracker()
    
    // Video URL (example)
    let videoURL = URL(fileURLWithPath: "/path/to/video.mp4")
    
    // MARK: - Frame Extraction
    
    // Extract frames from video (simplified - actual implementation uses VideoProcessor)
    let frames = try await extractFramesExample(from: videoURL, frameRate: 5)
    
    // MARK: - Object Detection
    
    print("Detecting objects in \(frames.count) frames...")
    var allDetections: [Detection] = []
    
    for frame in frames {
        // Detect objects in each frame
        let detections = try await objectDetector.detect(in: frame, sportType: .pickleball)
        allDetections.append(contentsOf: detections)
        
        print("Frame \(frame.frameNumber): \(detections.count) detections")
    }
    
    print("Total detections: \(allDetections.count)")
    
    // MARK: - Object Tracking
    
    print("\nTracking objects across frames...")
    let tracks = try await objectTracker.track(detections: allDetections)
    
    print("Generated \(tracks.count) tracks")
    
    // MARK: - Track Analysis
    
    // Analyze tracks by object class
    let tracksByClass = Dictionary(grouping: tracks) { $0.objectClass }
    
    for (objectClass, classTracks) in tracksByClass {
        print("\n\(objectClass.rawValue.capitalized) Tracks: \(classTracks.count)")
        
        for track in classTracks {
            print("  Track \(track.id):")
            print("    Detections: \(track.detections.count)")
            print("    Duration: \(String(format: "%.2f", track.duration))s")
            print("    Confidence: \(String(format: "%.2f", track.averageConfidence))")
            print("    Frames: \(track.detections.first!.frameNumber) - \(track.detections.last!.frameNumber)")
        }
    }
    
    // MARK: - Track Statistics
    
    let stats = objectTracker.computeTrackStatistics(tracks: tracks)
    
    print("\nTrack Statistics:")
    print("  Total tracks: \(stats.totalTracks)")
    print("  Average duration: \(String(format: "%.2f", stats.averageDuration))s")
    print("  Average confidence: \(String(format: "%.2f", stats.averageConfidence))")
    print("  Tracks by class:")
    for (objectClass, count) in stats.tracksByClass {
        print("    \(objectClass.rawValue): \(count)")
    }
    
    // MARK: - Track Trajectories
    
    // Analyze ball trajectories
    let ballTracks = tracks.filter { $0.objectClass == .ball }
    
    for track in ballTracks {
        let trajectory = track.trajectory
        print("\nBall Track \(track.id) Trajectory:")
        print("  Start: (\(String(format: "%.2f", trajectory.first!.x)), \(String(format: "%.2f", trajectory.first!.y)))")
        print("  End: (\(String(format: "%.2f", trajectory.last!.x)), \(String(format: "%.2f", trajectory.last!.y)))")
        print("  Points: \(trajectory.count)")
    }
}

/// Example: Custom tracking configuration
func exampleCustomTracking() async throws {
    // Create tracker with custom parameters
    let tracker = ObjectTracker(
        iouThreshold: 0.4,      // Stricter matching
        maxFrameGap: 20,        // Shorter re-identification window
        minConfidence: 0.4      // Higher confidence requirement
    )
    
    // Use custom tracker for high-quality video analysis
    // where objects are clearly visible and tracking should be precise
}

/// Example: Handling tracking errors
func exampleErrorHandling() async throws {
    let tracker = ObjectTracker()
    
    do {
        // Attempt tracking with empty detections
        let tracks = try await tracker.track(detections: [])
        print("Tracks: \(tracks.count)")
    } catch TrackingError.insufficientDetections {
        print("Error: No detections provided for tracking")
        // Handle error: skip tracking or use fallback
    } catch {
        print("Unexpected error: \(error)")
    }
}

/// Example: Track filtering and analysis
func exampleTrackFiltering(tracks: [Track]) {
    // Filter tracks by duration
    let longTracks = tracks.filter { $0.duration > 2.0 }
    print("Long tracks (>2s): \(longTracks.count)")
    
    // Filter tracks by confidence
    let highConfidenceTracks = tracks.filter { $0.averageConfidence > 0.7 }
    print("High confidence tracks (>0.7): \(highConfidenceTracks.count)")
    
    // Filter tracks by detection count
    let substantialTracks = tracks.filter { $0.detections.count >= 10 }
    print("Substantial tracks (>=10 detections): \(substantialTracks.count)")
    
    // Find longest track
    if let longestTrack = tracks.max(by: { $0.duration < $1.duration }) {
        print("Longest track: \(String(format: "%.2f", longestTrack.duration))s")
    }
    
    // Find highest confidence track
    if let bestTrack = tracks.max(by: { $0.averageConfidence < $1.averageConfidence }) {
        print("Highest confidence track: \(String(format: "%.2f", bestTrack.averageConfidence))")
    }
}

/// Example: Track visualization data
func exampleTrackVisualization(track: Track) {
    // Generate visualization data for a track
    struct TrackVisualization {
        let trackID: UUID
        let objectClass: ObjectClass
        let points: [(frame: Int, position: CGPoint, confidence: Float)]
        let color: String
    }
    
    let points = track.detections.map { detection in
        (
            frame: detection.frameNumber,
            position: CGPoint(x: detection.boundingBox.midX, y: detection.boundingBox.midY),
            confidence: detection.confidence
        )
    }
    
    let color = colorForObjectClass(track.objectClass)
    
    let visualization = TrackVisualization(
        trackID: track.id,
        objectClass: track.objectClass,
        points: points,
        color: color
    )
    
    print("Track visualization: \(visualization.points.count) points")
}

// MARK: - Helper Functions

/// Simplified frame extraction for example purposes
private func extractFramesExample(from url: URL, frameRate: Int) async throws -> [VideoFrame] {
    // This is a simplified example
    // Actual implementation would use VideoProcessor
    return []
}

/// Returns a color for visualizing different object classes
private func colorForObjectClass(_ objectClass: ObjectClass) -> String {
    switch objectClass {
    case .ball:
        return "yellow"
    case .player:
        return "blue"
    case .paddle:
        return "green"
    case .courtLine:
        return "white"
    case .net:
        return "gray"
    case .netPost:
        return "gray"
    }
}
