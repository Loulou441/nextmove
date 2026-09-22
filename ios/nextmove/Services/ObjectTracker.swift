//
//  ObjectTracker.swift
//  nextmove
//
//  Object tracking service using Vision framework for temporal tracking
//  Validates: Requirements 3.1-3.8, 14.2
//

import Foundation
import Vision
import CoreGraphics
import AVFoundation
import os.log

/// Maintains object identity across frames using Vision framework
/// Validates: Requirements 3.1-3.8, 14.2
final class ObjectTracker: ObjectTrackerProtocol {
    
    // MARK: - Properties
    
    /// Vision sequence request handler for temporal tracking
    private var sequenceHandler: VNSequenceRequestHandler?
    
    /// Active tracks being maintained across frames
    private var activeTracks: [UUID: TrackState] = [:]
    
    /// Completed tracks that have been terminated
    private var completedTracks: [Track] = []
    
    /// IoU threshold for matching detections to tracks (default 0.3)
    private let iouThreshold: Float
    
    /// Maximum frames without detection before terminating track (default 30)
    private let maxFrameGap: Int
    
    /// Minimum confidence threshold for maintaining tracks (default 0.3)
    private let minConfidence: Float
    
    /// Logger for debugging and observability
    private let logger = Logger(subsystem: "com.nextmove.cvml", category: "ObjectTracker")
    
    /// Lock for thread-safe track access
    private let trackLock = NSLock()
    
    // MARK: - Initialization
    
    /// Initializes the object tracker with configurable parameters
    /// - Parameters:
    ///   - iouThreshold: IoU threshold for detection-to-track matching (default 0.3)
    ///   - maxFrameGap: Maximum frames without detection before terminating (default 30)
    ///   - minConfidence: Minimum confidence threshold for tracks (default 0.3)
    init(
        iouThreshold: Float = 0.3,
        maxFrameGap: Int = 30,
        minConfidence: Float = 0.3
    ) {
        self.iouThreshold = iouThreshold
        self.maxFrameGap = maxFrameGap
        self.minConfidence = minConfidence
    }
    
    // MARK: - ObjectTrackerProtocol Implementation
    
    /// Tracks objects across multiple frames to maintain identity
    /// Validates: Requirements 3.1-3.8, 14.2, 14.5
    /// - Parameter detections: Array of detections from consecutive frames
    /// - Returns: Array of tracks with consistent object IDs
    /// - Throws: TrackingError
    func track(detections: [Detection]) async throws -> [Track] {
        trackLock.lock()
        defer { trackLock.unlock() }
        
        guard !detections.isEmpty else {
            logger.warning("No detections provided for tracking")
            throw TrackingError.insufficientDetections
        }
        
        // Initialize sequence handler if needed
        if sequenceHandler == nil {
            sequenceHandler = VNSequenceRequestHandler()
        }
        
        // Group detections by frame number
        let detectionsByFrame = Dictionary(grouping: detections) { $0.frameNumber }
        let sortedFrameNumbers = detectionsByFrame.keys.sorted()
        
        logger.info("Tracking \(detections.count) detections across \(sortedFrameNumbers.count) frames")
        
        // Process each frame sequentially
        for frameNumber in sortedFrameNumbers {
            guard let frameDetections = detectionsByFrame[frameNumber] else { continue }
            
            try processFrame(frameNumber: frameNumber, detections: frameDetections)
        }
        
        // Finalize all active tracks
        finalizeAllTracks()
        
        logger.info("Tracking complete: \(self.completedTracks.count) tracks generated")
        
        return self.completedTracks
    }
    
    // MARK: - Private Methods
    
    /// Processes detections for a single frame
    /// Validates: Requirements 3.1, 3.5, 3.7
    private func processFrame(frameNumber: Int, detections: [Detection]) throws {
        // Update frame gaps for all active tracks
        updateFrameGaps(currentFrame: frameNumber)
        
        // Match detections to existing tracks
        let (matched, unmatchedDetections) = matchDetectionsToTracks(detections: detections)
        
        // Update matched tracks
        for (trackID, detection) in matched {
            updateTrack(trackID: trackID, with: detection)
        }
        
        // Create new tracks for unmatched detections
        for detection in unmatchedDetections {
            createTrack(from: detection)
        }
        
        // Terminate tracks that exceed frame gap or confidence threshold
        terminateInvalidTracks()
    }
    
    /// Matches detections to existing tracks using IoU
    /// Validates: Requirements 3.1, 3.5
    private func matchDetectionsToTracks(
        detections: [Detection]
    ) -> (matched: [(UUID, Detection)], unmatched: [Detection]) {
        var matched: [(UUID, Detection)] = []
        var unmatchedDetections = detections
        var matchedTrackIDs = Set<UUID>()
        
        // For each active track, find best matching detection
        for (trackID, trackState) in activeTracks {
            guard let lastDetection = trackState.detections.last else { continue }
            
            // Find best matching detection (same class, highest IoU above threshold)
            var bestMatch: (detection: Detection, iou: Float)?
            
            for detection in unmatchedDetections {
                // Only match same object class
                guard detection.objectClass == trackState.objectClass else { continue }
                
                // Compute IoU
                let iou = computeIoU(
                    box1: lastDetection.boundingBox,
                    box2: detection.boundingBox
                )
                
                // Check if above threshold and better than current best
                if iou >= iouThreshold {
                    if let current = bestMatch {
                        if iou > current.iou {
                            bestMatch = (detection, iou)
                        }
                    } else {
                        bestMatch = (detection, iou)
                    }
                }
            }
            
            // If match found, record it
            if let match = bestMatch {
                matched.append((trackID, match.detection))
                matchedTrackIDs.insert(trackID)
                
                // Remove from unmatched
                if let index = unmatchedDetections.firstIndex(where: { $0.id == match.detection.id }) {
                    unmatchedDetections.remove(at: index)
                }
            }
        }
        
        return (matched, unmatchedDetections)
    }
    
    /// Computes Intersection over Union (IoU) between two bounding boxes
    /// Validates: Requirements 3.1
    private func computeIoU(box1: CGRect, box2: CGRect) -> Float {
        // Compute intersection
        let intersection = box1.intersection(box2)
        
        guard !intersection.isNull else {
            return 0.0
        }
        
        let intersectionArea = intersection.width * intersection.height
        
        // Compute union
        let box1Area = box1.width * box1.height
        let box2Area = box2.width * box2.height
        let unionArea = box1Area + box2Area - intersectionArea
        
        guard unionArea > 0 else {
            return 0.0
        }
        
        return Float(intersectionArea / unionArea)
    }
    
    /// Updates frame gaps for all active tracks
    /// Validates: Requirements 3.5, 3.7
    private func updateFrameGaps(currentFrame: Int) {
        for (trackID, trackState) in activeTracks {
            if let lastFrame = trackState.detections.last?.frameNumber {
                let gap = currentFrame - lastFrame
                activeTracks[trackID]?.frameGap = gap
            }
        }
    }
    
    /// Updates an existing track with a new detection
    /// Validates: Requirements 3.1, 3.8
    private func updateTrack(trackID: UUID, with detection: Detection) {
        guard var trackState = activeTracks[trackID] else { return }
        
        // Add detection to track
        trackState.detections.append(detection)
        trackState.frameGap = 0 // Reset frame gap
        trackState.lastUpdateFrame = detection.frameNumber
        
        // Update average confidence
        let totalConfidence = trackState.detections.reduce(0.0) { $0 + $1.confidence }
        trackState.averageConfidence = totalConfidence / Float(trackState.detections.count)
        
        activeTracks[trackID] = trackState
        
        logger.debug("Updated track \(trackID) with detection at frame \(detection.frameNumber)")
    }
    
    /// Creates a new track from an unmatched detection
    /// Validates: Requirements 3.1, 3.6
    private func createTrack(from detection: Detection) {
        let trackID = UUID()
        
        let trackState = TrackState(
            id: trackID,
            objectClass: detection.objectClass,
            detections: [detection],
            frameGap: 0,
            lastUpdateFrame: detection.frameNumber,
            averageConfidence: detection.confidence
        )
        
        activeTracks[trackID] = trackState
        
        logger.debug("Created new track \(trackID) for \(detection.objectClass.rawValue) at frame \(detection.frameNumber)")
    }
    
    /// Terminates tracks that exceed frame gap or fall below confidence threshold
    /// Validates: Requirements 3.5, 3.7
    private func terminateInvalidTracks() {
        var tracksToTerminate: [UUID] = []
        
        for (trackID, trackState) in activeTracks {
            // Check frame gap
            if trackState.frameGap > self.maxFrameGap {
                logger.debug("Terminating track \(trackID): frame gap \(trackState.frameGap) exceeds max \(self.maxFrameGap)")
                tracksToTerminate.append(trackID)
                continue
            }
            
            // Check confidence
            if trackState.averageConfidence < self.minConfidence {
                logger.debug("Terminating track \(trackID): confidence \(trackState.averageConfidence) below threshold \(self.minConfidence)")
                tracksToTerminate.append(trackID)
                continue
            }
        }
        
        // Finalize terminated tracks
        for trackID in tracksToTerminate {
            finalizeTrack(trackID: trackID)
        }
    }
    
    /// Finalizes a track and moves it to completed tracks
    /// Validates: Requirements 3.8
    private func finalizeTrack(trackID: UUID) {
        guard let trackState = activeTracks[trackID] else { return }
        
        // Only finalize tracks with at least one detection
        guard !trackState.detections.isEmpty else {
            activeTracks.removeValue(forKey: trackID)
            return
        }
        
        let track = Track(
            id: trackState.id,
            objectClass: trackState.objectClass,
            detections: trackState.detections,
            startTime: trackState.detections.first!.timestamp,
            endTime: trackState.detections.last!.timestamp,
            averageConfidence: trackState.averageConfidence
        )
        
        completedTracks.append(track)
        activeTracks.removeValue(forKey: trackID)
        
        logger.info("Finalized track \(trackID): \(track.detections.count) detections, duration \(String(format: "%.2f", track.duration))s")
    }
    
    /// Finalizes all active tracks
    /// Validates: Requirements 3.8
    private func finalizeAllTracks() {
        let trackIDs = Array(activeTracks.keys)
        for trackID in trackIDs {
            finalizeTrack(trackID: trackID)
        }
    }
    
    /// Resets the tracker state for a new tracking session
    func reset() {
        trackLock.lock()
        defer { trackLock.unlock() }
        
        activeTracks.removeAll()
        completedTracks.removeAll()
        sequenceHandler = nil
        
        logger.info("Tracker state reset")
    }
}

// MARK: - Track State

/// Internal state for an active track
private struct TrackState {
    let id: UUID
    let objectClass: ObjectClass
    var detections: [Detection]
    var frameGap: Int
    var lastUpdateFrame: Int
    var averageConfidence: Float
}

// MARK: - Track Statistics

extension ObjectTracker {
    
    /// Computes statistics for a set of tracks
    /// Validates: Requirements 3.8
    func computeTrackStatistics(tracks: [Track]) -> TrackStatistics {
        guard !tracks.isEmpty else {
            return TrackStatistics(
                totalTracks: 0,
                averageDuration: 0.0,
                averageConfidence: 0.0,
                tracksByClass: [:]
            )
        }
        
        let totalDuration = tracks.reduce(0.0) { $0 + $1.duration }
        let averageDuration = totalDuration / Double(tracks.count)
        
        let totalConfidence = tracks.reduce(0.0) { $0 + Double($1.averageConfidence) }
        let averageConfidence = Float(totalConfidence / Double(tracks.count))
        
        let tracksByClass = Dictionary(grouping: tracks) { $0.objectClass }
            .mapValues { $0.count }
        
        return TrackStatistics(
            totalTracks: tracks.count,
            averageDuration: averageDuration,
            averageConfidence: averageConfidence,
            tracksByClass: tracksByClass
        )
    }
}

/// Statistics for a set of tracks
struct TrackStatistics {
    let totalTracks: Int
    let averageDuration: TimeInterval
    let averageConfidence: Float
    let tracksByClass: [ObjectClass: Int]
}
