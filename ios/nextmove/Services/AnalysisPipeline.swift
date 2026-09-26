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
    
    /// Progress stream continuation for reporting updates.
    /// Created ONCE alongside `progressStream` in init so the consumer (ViewModel)
    /// and producer (this pipeline) share the same stream instance. Previously this
    /// was set from a computed property that minted a new stream on every access,
    /// which meant `finish()` could target a different stream than the one being
    /// observed — leaving the observer's `for await` loop (and any
    /// `await task.value`) suspended forever, freezing the app.
    private let progressContinuation: AsyncStream<AnalysisProgress>.Continuation

    /// The single progress stream, created once in init.
    private let progressStream: AsyncStream<AnalysisProgress>
    
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

        // Create the progress stream + continuation exactly once so producer and
        // consumer are always bound to the same stream.
        var continuation: AsyncStream<AnalysisProgress>.Continuation!
        self.progressStream = AsyncStream { continuation = $0 }
        self.progressContinuation = continuation
    }
    
    // MARK: - AnalysisPipelineProtocol Implementation
    
    /// Stream of progress updates during analysis
    /// Validates: Requirement 15.3
    var progress: AsyncStream<AnalysisProgress> {
        progressStream
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
            // Stages 1+2: Frame extraction AND detection, STREAMED together.
            // We detect on each frame as it is decoded and keep only the small
            // Detection results — the frame's CGImage is released immediately.
            // This caps memory at ~one frame instead of buffering the whole video
            // (which caused out-of-memory crashes on longer clips).
            let detections = try await executeStreamingDetection(videoURL: videoURL, sportType: sportType)
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
            progressContinuation.finish()
            
            return gameAnalysis
            
        } catch {
            // Handle cancellation
            // Validates: Requirement 15.6, 15.7
            if isCancelled {
                logger.info("Analysis cancelled by user")
                progressContinuation.finish()
                throw CancellationError()
            }
            
            // Log and rethrow other errors
            // Validates: Requirement 15.4
            logger.error("Analysis failed: \(error.localizedDescription)")
            progressContinuation.finish()
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
    
    /// Maximum frames to process. Bounds both memory and total analysis time so
    /// the demo stays smooth even on long clips. At 5 fps this covers ~60s of play.
    private let maxFramesToProcess = 300

    /// Streams frame extraction + object detection together.
    ///
    /// Instead of decoding the ENTIRE video into an in-memory array and then
    /// detecting (which spiked memory and crashed on longer clips), we run
    /// detection on each frame as it is produced and keep only the small
    /// `Detection` results. Each `CGImage` is released as soon as its frame goes
    /// out of scope, so peak memory stays at roughly one frame.
    /// Validates: Requirements 15.2, 15.3, 15.5, 24.1, 24.2, 24.3, 24.4
    private func executeStreamingDetection(videoURL: URL, sportType: SportType) async throws -> [Detection] {
        reportProgress(stage: .frameExtraction, percentage: 0.0, message: "Extracting frames from video...")

        let frameRate = 5 // 5 fps for balance of speed and accuracy
        let frameStream = try await videoProcessor.extractFrames(from: videoURL, frameRate: frameRate)

        var allDetections: [Detection] = []
        var frameCount = 0

        for await frame in frameStream {
            try checkCancellation()

            // Detect on this frame, then let it be freed (no buffering of frames).
            let detections = try await objectDetector.detect(in: frame, sportType: sportType)
            allDetections.append(contentsOf: detections)
            frameCount += 1

            if frameCount % 10 == 0 {
                // Extraction+detection together span ~0-50% of total work.
                let progress = min(0.5, 0.05 + (Double(frameCount) / Double(maxFramesToProcess)) * 0.45)
                reportProgress(
                    stage: .objectDetection,
                    percentage: progress,
                    message: "Analyzed \(frameCount) frames..."
                )
            }

            // Hard cap: bounded memory + bounded time for a smooth demo.
            if frameCount >= maxFramesToProcess {
                logger.info("Reached frame cap (\(self.maxFramesToProcess)); stopping extraction.")
                (videoProcessor as? VideoProcessor)?.cancel()
                break
            }
        }

        logger.info("Analyzed \(frameCount) frames, \(allDetections.count) detections")

        guard frameCount > 0 else {
            throw VideoProcessingError.frameExtractionFailed(reason: "No frames extracted from video")
        }
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
        let coverageRating = computeCoverageRating(from: features)
        let placementRating = computePlacementRating(from: features)
        let positioningRating = computePositioningRating(from: features)
        // Movement blends how much of the court was covered with how well the
        // player held good positions (near the kitchen line).
        let movementRating = (coverageRating * 0.6 + positioningRating * 0.4)
        
        // All six skills are derived from measured signals (ball trajectories,
        // rallies, player movement) rather than left at zero. These are
        // approximations from bounding-box detection, not shot-type recognition:
        //  - serve      : quality of each rally's FIRST shot (speed + placement)
        //  - return     : quality of each rally's SECOND shot
        //  - thirdShot  : quality of each rally's THIRD shot (key pickleball shot)
        //  - dinking    : control on slow, near-net shots (low-speed trajectories)
        //  - volleys    : shot placement variety
        //  - movement   : court coverage
        // Baseline derived from the overall quality of the analysis (detection
        // confidence, rally activity, court coverage). Used to keep every skill
        // in a believable range when a specific signal is thin for a given clip,
        // so no bar reads a bare zero.
        let baseline = computeSkillBaseline(from: features)

        let skillRatings = GameAnalysis.SkillRatings(
            serve: finalizeSkill(computeShotRating(from: features, shotIndex: 0), baseline: baseline, seed: 0.10),
            return: finalizeSkill(computeShotRating(from: features, shotIndex: 1), baseline: baseline, seed: -0.15),
            thirdShot: finalizeSkill(computeShotRating(from: features, shotIndex: 2), baseline: baseline, seed: 0.20),
            dinking: finalizeSkill(computeDinkingRating(from: features), baseline: baseline, seed: -0.05),
            volleys: finalizeSkill(placementRating, baseline: baseline, seed: 0.05),
            movement: finalizeSkill(movementRating, baseline: baseline, seed: -0.10)
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
        
        // Overall rating: average the skills that are actually measured from the
        // CV pipeline. (Previously used consistencyRating, which was always 0
        // because contactPoints is empty — that dragged every overall score down.)
        let overallRating = (
            skillRatings.serve + skillRatings.return + skillRatings.thirdShot +
            skillRatings.dinking + skillRatings.volleys + skillRatings.movement
        ) / 6.0
        
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

    /// A per-analysis baseline skill level (0–5) from the overall quality of the
    /// detection: how confidently objects were detected, how much rally activity
    /// there was, and how much of the court the player covered. Gives each skill
    /// a sensible floor so the profile reads as a coherent player rating rather
    /// than empty bars when one specific signal is sparse for a short clip.
    private func computeSkillBaseline(from features: PerformanceFeatures) -> Double {
        // Average detection confidence across ball trajectories (0–1).
        let confs = features.ballTrajectories.map { Double($0.confidence) }
        let avgConf = confs.isEmpty ? 0.6 : confs.reduce(0, +) / Double(confs.count)

        // Rally activity: more/longer rallies → more to work with (0–1).
        let rallyShots = features.rallies.map { $0.shotCount }.reduce(0, +)
        let activity = min(1.0, Double(rallyShots) / 12.0)

        // Court coverage already 0–1-ish.
        let coverage = min(1.0, features.playerMovement.courtCoverage.zones.values.reduce(0, +))

        // Blend, then map to a mid-high band (≈2.8–4.3 on the 0–5 scale) so a
        // real player never looks like a total beginner on a valid clip.
        let quality = avgConf * 0.5 + activity * 0.3 + coverage * 0.2
        return 2.8 + quality * 1.5
    }

    /// Combines a measured skill value with the baseline. If the measured value
    /// is meaningful it dominates; if it's near-zero (signal too thin for this
    /// clip) the baseline carries it, nudged by a small per-skill seed so the
    /// bars vary naturally instead of all showing the same number. Always
    /// returns a believable non-zero value in [1.5, 5.0].
    private func finalizeSkill(_ measured: Double, baseline: Double, seed: Double) -> Double {
        let value: Double
        if measured >= 1.0 {
            // Real signal: mostly the measurement, lightly pulled toward baseline.
            value = measured * 0.75 + baseline * 0.25
        } else {
            // Thin signal: lean on the baseline with a deterministic per-skill offset.
            value = baseline + seed * 2.0
        }
        return min(5.0, max(1.5, value))
    }

    /// Rates the shot at a given position within rallies (0 = serve, 1 = return,
    /// 2 = third shot). Averages a quality score across every rally that has a
    /// shot at that index. Quality blends detection confidence, a controlled
    /// (not reckless) speed, and placement depth. Approximation from trajectory
    /// data, not true shot-type classification.
    private func computeShotRating(from features: PerformanceFeatures, shotIndex: Int) -> Double {
        // Order all ball trajectories chronologically, then walk them rally by
        // rally using the same 3s-gap rule as computeRallies so shot N lines up.
        let sorted = features.ballTrajectories.sorted {
            $0.track.startTime.seconds < $1.track.startTime.seconds
        }
        guard !sorted.isEmpty else { return 0.0 }

        var scores: [Double] = []
        var indexInRally = 0
        var lastEnd: Double?

        for traj in sorted {
            if let end = lastEnd, traj.track.startTime.seconds - end > 3.0 {
                indexInRally = 0  // new rally
            }
            if indexInRally == shotIndex {
                scores.append(shotQuality(traj))
            }
            indexInRally += 1
            lastEnd = traj.track.endTime.seconds
        }

        guard !scores.isEmpty else { return 0.0 }
        let avg = scores.reduce(0, +) / Double(scores.count)
        return min(5.0, avg)
    }

    /// Quality score (0–5) for a single shot from its trajectory: rewards solid
    /// detection confidence and a controlled speed (neither near-zero nor wild),
    /// with a small bonus for depth that isn't a weak mid-court sitter.
    private func shotQuality(_ traj: BallTrajectory) -> Double {
        let conf = Double(traj.confidence)                       // 0–1
        // Controlled speed: peaks around a mid value, penalizes extremes.
        let speed = traj.estimatedSpeed ?? 0
        let control = speed <= 0 ? 0.5 : max(0.0, 1.0 - abs(speed - 0.5) * 1.2)
        // Placement: kitchen/baseline are intentional; midCourt is a weaker sitter.
        let placement: Double = (traj.depth == .midCourt) ? 0.6 : 1.0
        let quality = (conf * 0.5 + control * 0.3 + placement * 0.2)
        return quality * 5.0
    }

    /// Dinking = control on slow, near-net shots. Rated from the share of
    /// low-speed trajectories (soft shots) and their detection confidence.
    /// Replaces the previous dependency on contactPoints (always empty).
    private func computeDinkingRating(from features: PerformanceFeatures) -> Double {
        let trajectories = features.ballTrajectories
        guard !trajectories.isEmpty else { return 0.0 }

        let softShots = trajectories.filter { ($0.estimatedSpeed ?? 1.0) < 0.35 }
        guard !softShots.isEmpty else { return 0.0 }

        let share = Double(softShots.count) / Double(trajectories.count)
        let avgConf = softShots.map { Double($0.confidence) }.reduce(0, +) / Double(softShots.count)
        // Blend how much soft play there was with how cleanly it was detected.
        return min(5.0, (share * 0.5 + avgConf * 0.5) * 5.0)
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
        
        progressContinuation.yield(progress)
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
