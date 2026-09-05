//
//  AnalysisPipeline.swift
//  nextmove
//
//  Orchestrates end-to-end video analysis workflow
//  Validates: Requirements 15.1-15.8, 24.1-24.8
//

import Foundation
import CoreML
import AVFoundation
import os.log

/// Orchestrates the complete video analysis pipeline from frame extraction to coaching feedback
/// Executes stages sequentially with progress reporting and cancellation support
/// Validates: Requirements 15.1-15.8, 24.1-24.8
final class AnalysisPipeline: AnalysisPipelineProtocol {
    
    // MARK: - Properties
    
    /// Component dependencies
    private let videoProcessor: VideoProcessorProtocol
    private let objectDetector: ObjectDetectorProtocol
    private let objectTracker: ObjectTrackerProtocol
    private let featureExtractor: FeatureExtractorProtocol
    private let coachingEngine: CoachingEngineProtocol
    private let modelManager: ModelManagerProtocol
    
    /// Progress stream continuation for reporting updates
    private var progressContinuation: AsyncStream<AnalysisProgress>.Continuation?
    
    /// Cancellation flag
    private var isCancelled = false
    
    /// Lock for thread-safe cancellation
    private let cancellationLock = NSLock()
    
    /// Logger for debugging and observability
    private let logger = Logger(subsystem: "com.nextmove.cvml", category: "AnalysisPipeline")
    
    /// Background queue for analysis execution
    private let analysisQueue = DispatchQueue(label: "com.nextmove.analysis", qos: .userInitiated)
    
    // MARK: - Initialization
    
    /// Initializes the analysis pipeline with all component dependencies
    /// Validates: Requirements 15.1, 15.2
    /// - Parameters:
    ///   - videoProcessor: Component for extracting frames from video
    ///   - objectDetector: Component for detecting objects in frames
    ///   - objectTracker: Component for tracking objects across frames
    ///   - featureExtractor: Component for extracting performance metrics
    ///   - coachingEngine: Component for generating coaching feedback
    ///   - modelManager: Component for managing Core ML models
    init(
        videoProcessor: VideoProcessorProtocol,
        objectDetector: ObjectDetectorProtocol,
        objectTracker: ObjectTrackerProtocol,
        featureExtractor: FeatureExtractorProtocol,
        coachingEngine: CoachingEngineProtocol,
        modelManager: ModelManagerProtocol
    ) {
        self.videoProcessor = videoProcessor
        self.objectDetector = objectDetector
        self.objectTracker = objectTracker
        self.featureExtractor = featureExtractor
        self.coachingEngine = coachingEngine
        self.modelManager = modelManager
    }
    
    // MARK: - AnalysisPipelineProtocol Implementation
    
    /// Stream of progress updates during analysis
    /// Validates: Requirement 15.3
    var progress: AsyncStream<AnalysisProgress> {
        AsyncStream { continuation in
            self.progressContinuation = continuation
        }
    }
    
    /// Analyzes a game recording and returns complete analysis results
    /// Executes stages sequentially: frame extraction → detection → tracking → features → coaching
    /// Validates: Requirements 15.1-15.8, 24.1-24.8
    /// - Parameters:
    ///   - recording: The game recording to analyze
    ///   - sportType: The sport type for sport-specific processing
    /// - Returns: Complete GameAnalysis with coaching feedback and metrics
    /// - Throws: VideoProcessingError, ModelLoadingError, InsufficientDataError, CancellationError
    func analyze(recording: GameRecording, sportType: SportType) async throws -> GameAnalysis {
        let startTime = CFAbsoluteTimeGetCurrent()
        
        logger.info("Starting analysis for recording \(recording.id) (\(sportType.rawValue))")
        
        // Reset cancellation flag
        cancellationLock.lock()
        isCancelled = false
        cancellationLock.unlock()
        
        // Validate video URL
        guard let videoURL = recording.videoURL else {
            throw VideoProcessingError.fileNotFound
        }
        
        do {
            // Stage 1: Frame Extraction
            // Validates: Requirements 15.2, 15.5, 24.1
            let frames = try await executeFrameExtraction(videoURL: videoURL)
            try checkCancellation()
            
            // Stage 2: Object Detection
            // Validates: Requirements 15.2, 15.5, 24.2, 24.3, 24.4
            let detections = try await executeObjectDetection(frames: frames, sportType: sportType)
            try checkCancellation()
            
            // Stage 3: Object Tracking
            // Validates: Requirements 15.2, 15.5
            let tracks = try await executeObjectTracking(detections: detections)
            try checkCancellation()
            
            // Stage 4: Feature Extraction
            // Validates: Requirements 15.2, 15.5
            let features = try await executeFeatureExtraction(tracks: tracks, sportType: sportType)
            try checkCancellation()
            
            // Stage 5: Coaching Generation
            // Validates: Requirements 15.2, 15.5
            let coachingFeedback = try await executeCoachingGeneration(features: features, sportType: sportType)
            try checkCancellation()
            
            // Create GameAnalysis from results
            // Validates: Requirements 15.2
            let gameAnalysis = createGameAnalysis(from: features, coaching: coachingFeedback)
            
            let totalTime = CFAbsoluteTimeGetCurrent() - startTime
            logger.info("Analysis completed in \(String(format: "%.2f", totalTime))s")
            
            // Validate performance target (< 2 minutes for 5-minute video)
            // Validates: Requirement 15.8
            if recording.duration > 0 {
                let targetTime = (recording.duration / 300.0) * 120.0 // Scale: 2 min for 5 min video
                if totalTime > targetTime {
                    logger.warning("Analysis exceeded target time: \(String(format: "%.2f", totalTime))s > \(String(format: "%.2f", targetTime))s")
                }
            }
            
            // Finish progress stream
            progressContinuation?.finish()
            
            return gameAnalysis
            
        } catch {
            // Handle cancellation
            // Validates: Requirement 15.6, 15.7
            if isCancelled {
                logger.info("Analysis cancelled by user")
                progressContinuation?.finish()
                throw CancellationError()
            }
            
            // Log and rethrow other errors
            // Validates: Requirement 15.4
            logger.error("Analysis failed: \(error.localizedDescription)")
            progressContinuation?.finish()
            throw error
        }
    }
    
    /// Cancels the current analysis operation
    /// Validates: Requirements 15.6, 15.7
    func cancel() {
        cancellationLock.lock()
        isCancelled = true
        cancellationLock.unlock()
        
        logger.info("Analysis cancellation requested")
    }
    
    // MARK: - Private Methods - Stage Execution
    
    /// Executes frame extraction stage
    /// Validates: Requirements 15.2, 15.3, 15.5, 24.1
    private func executeFrameExtraction(videoURL: URL) async throws -> [VideoFrame] {
        reportProgress(stage: .frameExtraction, percentage: 0.0, message: "Extracting frames from video...")
        
        let frameRate = 5 // 5 fps for balance of speed and accuracy
        let frameStream = try await videoProcessor.extractFrames(from: videoURL, frameRate: frameRate)
        
        var frames: [VideoFrame] = []
        var frameCount = 0
        
        for await frame in frameStream {
            try checkCancellation()
            
            frames.append(frame)
            frameCount += 1
            
            // Update progress periodically
            if frameCount % 10 == 0 {
                let percentage = 0.2 // Frame extraction is ~20% of total work
                reportProgress(
                    stage: .frameExtraction,
                    percentage: percentage,
                    message: "Extracted \(frameCount) frames..."
                )
            }
        }
        
        logger.info("Extracted \(frames.count) frames")
        
        guard !frames.isEmpty else {
            throw VideoProcessingError.frameExtractionFailed(reason: "No frames extracted from video")
        }
        
        reportProgress(stage: .frameExtraction, percentage: 0.2, message: "Frame extraction complete")
        
        return frames
    }
    
    /// Executes object detection stage
    /// Validates: Requirements 15.2, 15.3, 15.5, 24.2, 24.3, 24.4
    private func executeObjectDetection(frames: [VideoFrame], sportType: SportType) async throws -> [Detection] {
        reportProgress(stage: .objectDetection, percentage: 0.2, message: "Detecting objects in frames...")
        
        var allDetections: [Detection] = []
        let totalFrames = frames.count
        
        // Process frames sequentially (could be parallelized in future optimization)
        // Validates: Requirement 24.2
        for (index, frame) in frames.enumerated() {
            try checkCancellation()
            
            let detections = try await objectDetector.detect(in: frame, sportType: sportType)
            allDetections.append(contentsOf: detections)
            
            // Update progress
            let frameProgress = Double(index + 1) / Double(totalFrames)
            let overallProgress = 0.2 + (frameProgress * 0.3) // Detection is 20-50% of total work
            
            if (index + 1) % 10 == 0 || index == totalFrames - 1 {
                reportProgress(
                    stage: .objectDetection,
                    percentage: overallProgress,
                    message: "Detected objects in \(index + 1)/\(totalFrames) frames..."
                )
            }
        }
        
        logger.info("Detected \(allDetections.count) objects across \(totalFrames) frames")
        
        guard !allDetections.isEmpty else {
            throw InsufficientDataError(component: "object detection")
        }
        
        reportProgress(stage: .objectDetection, percentage: 0.5, message: "Object detection complete")
        
        return allDetections
    }
    
    /// Executes object tracking stage
    /// Validates: Requirements 15.2, 15.3, 15.5
    private func executeObjectTracking(detections: [Detection]) async throws -> [Track] {
        reportProgress(stage: .objectTracking, percentage: 0.5, message: "Tracking objects across frames...")
        
        let tracks = try await objectTracker.track(detections: detections)
        
        logger.info("Generated \(tracks.count) tracks")
        
        guard !tracks.isEmpty else {
            throw InsufficientDataError(component: "object tracking")
        }
        
        reportProgress(stage: .objectTracking, percentage: 0.65, message: "Object tracking complete")
        
        return tracks
    }
    
    /// Executes feature extraction stage
    /// Validates: Requirements 15.2, 15.3, 15.5
    private func executeFeatureExtraction(tracks: [Track], sportType: SportType) async throws -> PerformanceFeatures {
        reportProgress(stage: .featureExtraction, percentage: 0.65, message: "Extracting performance metrics...")
        
        let features = try await featureExtractor.extractFeatures(from: tracks, sportType: sportType)
        
        logger.info("Extracted features: \(features.ballTrajectories.count) trajectories, \(features.rallies.count) rallies, \(features.issues.count) issues")
        
        guard features.confidence > 0.0 else {
            throw InsufficientDataError(component: "feature extraction")
        }
        
        reportProgress(stage: .featureExtraction, percentage: 0.8, message: "Feature extraction complete")
        
        return features
    }
    
    /// Executes coaching generation stage
    /// Validates: Requirements 15.2, 15.3, 15.5
    private func executeCoachingGeneration(features: PerformanceFeatures, sportType: SportType) async throws -> CoachingFeedback {
        reportProgress(stage: .coachingGeneration, percentage: 0.8, message: "Generating coaching feedback...")
        
        let coaching = try await coachingEngine.generateCoaching(from: features, sportType: sportType)
        
        logger.info("Generated \(coaching.insights.count) insights, \(coaching.practiceSuggestions.count) practice suggestions")
        
        reportProgress(stage: .coachingGeneration, percentage: 0.95, message: "Coaching generation complete")
        
        return coaching
    }
    
    // MARK: - Private Methods - GameAnalysis Creation
    
    /// Creates GameAnalysis from performance features and coaching feedback
    /// Validates: Requirements 15.2
    private func createGameAnalysis(from features: PerformanceFeatures, coaching: CoachingFeedback) -> GameAnalysis {
        // Compute skill ratings from features
        let positioningRating = computePositioningRating(from: features)
        let consistencyRating = computeConsistencyRating(from: features)
        let coverageRating = computeCoverageRating(from: features)
        let placementRating = computePlacementRating(from: features)
        
        let skillRatings = GameAnalysis.SkillRatings(
            serve: 0.0, // Not detected in MVP
            return: 0.0, // Not detected in MVP
            thirdShot: 0.0, // Not detected in MVP
            dinking: consistencyRating,
            volleys: placementRating,
            movement: coverageRating
        )
        
        // Compute statistics
        let statistics = GameAnalysis.GameStatistics(
            totalRallies: features.rallies.count,
            longestRally: features.rallies.map { $0.shotCount }.max() ?? 0,
            winners: features.rallies.filter { $0.outcome == .winner }.count,
            errors: features.rallies.filter { $0.outcome == .error }.count,
            attacksAttempted: 0, // Not detected in MVP
            attacksSuccessful: 0, // Not detected in MVP
            courtCoveragePercent: features.playerMovement.courtCoverage.zones.values.reduce(0, +) * 100
        )
        
        // Create highlights from rallies
        let highlights = createHighlights(from: features)
        
        // Create heat map from positioning history
        let heatMap = createHeatMap(from: features)
        
        // Compute overall rating
        let overallRating = (positioningRating + consistencyRating + coverageRating + placementRating) / 4.0
        
        return GameAnalysis(
            overallRating: overallRating,
            skillRatings: skillRatings,
            statistics: statistics,
            highlights: highlights,
            heatMap: heatMap
        )
    }
    
    /// Computes positioning skill rating from features
    private func computePositioningRating(from features: PerformanceFeatures) -> Double {
        let positions = features.playerMovement.positioningHistory
        
        guard !positions.isEmpty else {
            return 0.0
        }
        
        // Rating based on optimal positioning percentage (near kitchen line: y > 0.6 && y < 0.8)
        let optimalCount = positions.filter { $0.y > 0.6 && $0.y < 0.8 }.count
        let optimalPercentage = Double(optimalCount) / Double(positions.count)
        
        return optimalPercentage * 5.0 // Scale to 0-5
    }
    
    /// Computes consistency skill rating from features
    private func computeConsistencyRating(from features: PerformanceFeatures) -> Double {
        let contacts = features.contactPoints
        
        guard !contacts.isEmpty else {
            return 0.0
        }
        
        // Rating based on on-time contact percentage
        let onTimeCount = contacts.filter { $0.timing == .onTime }.count
        let consistency = Double(onTimeCount) / Double(contacts.count)
        
        return consistency * 5.0 // Scale to 0-5
    }
    
    /// Computes coverage skill rating from features
    private func computeCoverageRating(from features: PerformanceFeatures) -> Double {
        let coverage = features.playerMovement.courtCoverage
        
        // Rating based on court coverage and balance
        let coverageScore = coverage.zones.values.reduce(0, +)
        let balanceScore = 1.0 - abs(coverage.leftRightBalance)
        
        return (coverageScore * 0.6 + balanceScore * 0.4) * 5.0 // Scale to 0-5
    }
    
    /// Computes placement skill rating from features
    private func computePlacementRating(from features: PerformanceFeatures) -> Double {
        let trajectories = features.ballTrajectories
        
        guard !trajectories.isEmpty else {
            return 0.0
        }
        
        // Rating based on shot variety (depth and direction)
        let depthVariety = Set(trajectories.map { $0.depth }).count
        let directionVariety = Set(trajectories.map { $0.direction }).count
        
        let variety = (Double(depthVariety) / 3.0 + Double(directionVariety) / 3.0) / 2.0
        
        return variety * 5.0 // Scale to 0-5
    }
    
    /// Creates highlights from performance features
    private func createHighlights(from features: PerformanceFeatures) -> [GameAnalysis.Highlight] {
        var highlights: [GameAnalysis.Highlight] = []
        
        // Add rally-ending winners
        for rally in features.rallies where rally.outcome == .winner {
            highlights.append(GameAnalysis.Highlight(
                type: .winner,
                timestamp: rally.endTime.seconds,
                duration: 5.0,
                description: "Rally-ending winner"
            ))
        }
        
        // Add long rallies (> 10 shots)
        for rally in features.rallies where rally.shotCount > 10 {
            highlights.append(GameAnalysis.Highlight(
                type: .longRally,
                timestamp: rally.startTime.seconds,
                duration: rally.duration,
                description: "\(rally.shotCount)-shot rally"
            ))
        }
        
        // Sort by timestamp and limit to top 10
        highlights.sort { $0.timestamp < $1.timestamp }
        return Array(highlights.prefix(10))
    }
    
    /// Creates heat map from positioning history
    private func createHeatMap(from features: PerformanceFeatures) -> GameAnalysis.CourtHeatMap {
        let positions = features.playerMovement.positioningHistory.map { position in
            GameAnalysis.CourtHeatMap.CourtPosition(
                x: position.x,
                y: position.y,
                intensity: 1.0
            )
        }
        
        return GameAnalysis.CourtHeatMap(positions: positions)
    }
    
    // MARK: - Private Methods - Progress and Cancellation
    
    /// Reports progress update
    /// Validates: Requirement 15.3
    private func reportProgress(stage: AnalysisStage, percentage: Double, message: String) {
        let progress = AnalysisProgress(
            stage: stage,
            percentage: percentage,
            message: message
        )
        
        progressContinuation?.yield(progress)
        logger.debug("Progress: \(stage.rawValue) - \(String(format: "%.1f", percentage * 100))% - \(message)")
    }
    
    /// Checks if analysis has been cancelled
    /// Validates: Requirements 15.6, 15.7
    private func checkCancellation() throws {
        cancellationLock.lock()
        let cancelled = isCancelled
        cancellationLock.unlock()
        
        if cancelled {
            throw CancellationError()
        }
    }
}

// MARK: - Cancellation Error

/// Error thrown when analysis is cancelled by user
/// Validates: Requirements 15.6, 15.7
struct CancellationError: Error, LocalizedError {
    var errorDescription: String? {
        return "Analysis was cancelled by user"
    }
}
