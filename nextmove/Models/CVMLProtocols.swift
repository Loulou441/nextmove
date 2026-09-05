//
//  CVMLProtocols.swift
//  nextmove
//
//  Component protocols for CV/ML video analysis pipeline
//  Validates: Requirements 15.1-15.8, 26.1-26.6
//

import Foundation
import CoreML
import AVFoundation

// MARK: - Analysis Pipeline Protocol

/// Orchestrates end-to-end analysis workflow with progress reporting and cancellation support
/// Validates: Requirements 15.1-15.8
protocol AnalysisPipelineProtocol {
    /// Analyzes a game recording and returns complete analysis results
    /// - Parameters:
    ///   - recording: The game recording to analyze
    ///   - sportType: The sport type for sport-specific processing
    /// - Returns: Complete GameAnalysis with coaching feedback and metrics
    /// - Throws: VideoProcessingError, ModelLoadingError, InsufficientDataError, CancellationError
    func analyze(recording: GameRecording, sportType: SportType) async throws -> GameAnalysis
    
    /// Cancels the current analysis operation
    func cancel()
    
    /// Stream of progress updates during analysis
    var progress: AsyncStream<AnalysisProgress> { get }
}

/// Progress information for analysis pipeline stages
struct AnalysisProgress {
    let stage: AnalysisStage
    let percentage: Double // 0.0-1.0
    let message: String
    
    init(stage: AnalysisStage, percentage: Double, message: String) {
        self.stage = stage
        self.percentage = percentage
        self.message = message
    }
}

/// Stages of the analysis pipeline
enum AnalysisStage: String, Codable {
    case frameExtraction
    case objectDetection
    case objectTracking
    case featureExtraction
    case coachingGeneration
}

// MARK: - Video Processor Protocol

/// Extracts frames from video files using AVFoundation
/// Validates: Requirements 1.1-1.7
protocol VideoProcessorProtocol {
    /// Extracts frames from a video file at the specified frame rate
    /// - Parameters:
    ///   - url: URL of the video file
    ///   - frameRate: Desired frame rate (1-30 fps)
    /// - Returns: AsyncStream of video frames with timestamps
    /// - Throws: VideoProcessingError if extraction fails
    func extractFrames(from url: URL, frameRate: Int) async throws -> AsyncStream<VideoFrame>
}

// MARK: - Object Detector Protocol

/// Identifies objects in video frames using Core ML models
/// Validates: Requirements 2.1-2.10, 14.1-14.5
protocol ObjectDetectorProtocol {
    /// Detects objects in a single video frame
    /// - Parameters:
    ///   - frame: The video frame to analyze
    ///   - sportType: Sport type for loading appropriate detection model
    /// - Returns: Array of detections with bounding boxes and confidence scores
    /// - Throws: ModelLoadingError, DetectionError
    func detect(in frame: VideoFrame, sportType: SportType) async throws -> [Detection]
}

// MARK: - Object Tracker Protocol

/// Maintains object identity across frames using Vision framework
/// Validates: Requirements 3.1-3.8, 14.2
protocol ObjectTrackerProtocol {
    /// Tracks objects across multiple frames to maintain identity
    /// - Parameter detections: Array of detections from consecutive frames
    /// - Returns: Array of tracks with consistent object IDs
    /// - Throws: TrackingError
    func track(detections: [Detection]) async throws -> [Track]
}

// MARK: - Feature Extractor Protocol

/// Derives performance metrics from object tracks
/// Validates: Requirements 4.1-4.7, 5.1-5.8, 6.1-6.7, 7.1-7.6
protocol FeatureExtractorProtocol {
    /// Extracts performance features from object tracks
    /// - Parameters:
    ///   - tracks: Array of object tracks from video analysis
    ///   - sportType: Sport type for sport-specific feature extraction
    /// - Returns: Performance features including trajectories, movement, contacts, and issues
    /// - Throws: FeatureExtractionError
    func extractFeatures(from tracks: [Track], sportType: SportType) async throws -> PerformanceFeatures
}

// MARK: - Coaching Engine Protocol

/// Translates performance metrics into human-readable feedback
/// Validates: Requirements 8.1-8.10
protocol CoachingEngineProtocol {
    /// Generates coaching feedback from performance features
    /// - Parameters:
    ///   - features: Performance features extracted from video analysis
    ///   - sportType: Sport type for sport-specific coaching templates
    /// - Returns: Coaching feedback with insights, suggestions, and tips
    /// - Throws: CoachingGenerationError
    func generateCoaching(from features: PerformanceFeatures, sportType: SportType) async throws -> CoachingFeedback
}

// MARK: - Model Manager Protocol

/// Loads and manages Core ML models
/// Validates: Requirements 13.1-13.8, 28.1-28.7
protocol ModelManagerProtocol {
    /// Loads a Core ML model for the specified sport and version
    /// - Parameters:
    ///   - sportType: Sport type to load model for
    ///   - version: Optional model version (defaults to latest)
    /// - Returns: Loaded MLModel instance
    /// - Throws: ModelLoadingError, ModelNotFoundError, IncompatibleVersionError
    func loadModel(for sportType: SportType, version: String?) async throws -> MLModel
    
    /// Releases cached models to free memory
    func releaseModels()
}

// MARK: - Persistence Service Protocol

/// Saves and loads analysis results and intermediate data
/// Validates: Requirements 22.1-22.8
protocol PersistenceServiceProtocol {
    /// Saves game analysis results
    /// - Parameters:
    ///   - analysis: The game analysis to save
    ///   - recording: The associated game recording
    /// - Throws: PersistenceError
    func save(analysis: GameAnalysis, for recording: GameRecording) async throws
    
    /// Saves track data for debugging or re-analysis
    /// - Parameters:
    ///   - tracks: Array of tracks to save
    ///   - recording: The associated game recording
    /// - Throws: PersistenceError
    func save(tracks: [Track], for recording: GameRecording) async throws
    
    /// Loads previously saved track data
    /// - Parameter recording: The game recording to load tracks for
    /// - Returns: Array of tracks
    /// - Throws: PersistenceError
    func loadTracks(for recording: GameRecording) async throws -> [Track]
}

// MARK: - Error Types

/// Errors that can occur during video processing
enum VideoProcessingError: Error, LocalizedError, Equatable {
    case invalidVideoFormat
    case frameExtractionFailed(reason: String)
    case unsupportedDuration
    case fileNotFound
    
    var errorDescription: String? {
        switch self {
        case .invalidVideoFormat:
            return "The video format is not supported. Please use MP4, MOV, or M4V."
        case .frameExtractionFailed(let reason):
            return "Failed to extract frames: \(reason)"
        case .unsupportedDuration:
            return "Video duration exceeds the maximum supported length of 60 minutes."
        case .fileNotFound:
            return "Video file not found at the specified location."
        }
    }
}

/// Errors that can occur during model loading
enum ModelLoadingError: Error, LocalizedError {
    case modelNotFound(sportType: SportType, version: String?)
    case incompatibleVersion(required: String, current: String)
    case compilationFailed(reason: String)
    case memoryAllocationFailed
    
    var errorDescription: String? {
        switch self {
        case .modelNotFound(let sportType, let version):
            let versionStr = version.map { " version \($0)" } ?? ""
            return "Model for \(sportType.rawValue)\(versionStr) not found in app bundle."
        case .incompatibleVersion(let required, let current):
            return "Model requires iOS \(required) but current version is \(current)."
        case .compilationFailed(let reason):
            return "Failed to compile model: \(reason)"
        case .memoryAllocationFailed:
            return "Insufficient memory to load model."
        }
    }
}

/// Errors that can occur during object detection
enum DetectionError: Error, LocalizedError {
    case inferenceFailure(reason: String)
    case invalidInput
    
    var errorDescription: String? {
        switch self {
        case .inferenceFailure(let reason):
            return "Detection inference failed: \(reason)"
        case .invalidInput:
            return "Invalid input frame for detection."
        }
    }
}

/// Errors that can occur during object tracking
enum TrackingError: Error, LocalizedError {
    case trackingFailure(reason: String)
    case insufficientDetections
    
    var errorDescription: String? {
        switch self {
        case .trackingFailure(let reason):
            return "Object tracking failed: \(reason)"
        case .insufficientDetections:
            return "Not enough detections to establish tracks."
        }
    }
}

/// Errors that can occur during feature extraction
enum FeatureExtractionError: Error, LocalizedError {
    case insufficientData(component: String)
    case invalidTrackData
    
    var errorDescription: String? {
        switch self {
        case .insufficientData(let component):
            return "Insufficient data for \(component) analysis."
        case .invalidTrackData:
            return "Track data is invalid or corrupted."
        }
    }
}

/// Errors that can occur during coaching generation
enum CoachingGenerationError: Error, LocalizedError {
    case insufficientFeatures
    case templateNotFound(sportType: SportType)
    
    var errorDescription: String? {
        switch self {
        case .insufficientFeatures:
            return "Not enough performance data to generate coaching feedback."
        case .templateNotFound(let sportType):
            return "Coaching templates for \(sportType.rawValue) not found."
        }
    }
}

/// Errors that can occur during data persistence
enum PersistenceError: Error, LocalizedError {
    case saveFailed(reason: String)
    case loadFailed(reason: String)
    case dataCorrupted
    case storageQuotaExceeded
    
    var errorDescription: String? {
        switch self {
        case .saveFailed(let reason):
            return "Failed to save data: \(reason)"
        case .loadFailed(let reason):
            return "Failed to load data: \(reason)"
        case .dataCorrupted:
            return "Stored data is corrupted and cannot be loaded."
        case .storageQuotaExceeded:
            return "Storage quota exceeded. Please free up space."
        }
    }
}

/// Error indicating insufficient data for analysis
struct InsufficientDataError: Error, LocalizedError {
    let component: String
    
    var errorDescription: String? {
        return "Insufficient data from \(component) to complete analysis."
    }
}
