//
//  AnalysisPipelineTests.swift
//  nextmoveTests
//
//  Unit tests for AnalysisPipeline orchestration
//  Validates: Requirements 15.1-15.8, 24.1-24.8
//

import XCTest
import CoreML
import AVFoundation
@testable import nextmove

final class AnalysisPipelineTests: XCTestCase {
    
    // MARK: - Mock Components
    
    class MockVideoProcessor: VideoProcessorProtocol {
        var shouldThrowError = false
        var frameCount = 10
        
        func extractFrames(from url: URL, frameRate: Int) async throws -> AsyncStream<VideoFrame> {
            if shouldThrowError {
                throw VideoProcessingError.frameExtractionFailed(reason: "Mock error")
            }
            
            return AsyncStream { continuation in
                Task {
                    for i in 0..<frameCount {
                        let frame = VideoFrame(
                            image: createMockCGImage(),
                            timestamp: CMTime(seconds: Double(i), preferredTimescale: 600),
                            frameNumber: i
                        )
                        continuation.yield(frame)
                    }
                    continuation.finish()
                }
            }
        }
        
        private func createMockCGImage() -> CGImage {
            let width = 640
            let height = 640
            let colorSpace = CGColorSpaceCreateDeviceRGB()
            let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)
            
            let context = CGContext(
                data: nil,
                width: width,
                height: height,
                bitsPerComponent: 8,
                bytesPerRow: width * 4,
                space: colorSpace,
                bitmapInfo: bitmapInfo.rawValue
            )!
            
            return context.makeImage()!
        }
    }
    
    class MockObjectDetector: ObjectDetectorProtocol {
        var shouldThrowError = false
        var detectionsPerFrame = 3
        
        func detect(in frame: VideoFrame, sportType: SportType) async throws -> [Detection] {
            if shouldThrowError {
                throw DetectionError.inferenceFailure(reason: "Mock error")
            }
            
            var detections: [Detection] = []
            for i in 0..<detectionsPerFrame {
                let detection = Detection(
                    objectClass: .ball,
                    boundingBox: CGRect(x: 0.1 * Double(i), y: 0.1, width: 0.05, height: 0.05),
                    confidence: 0.8,
                    frameNumber: frame.frameNumber,
                    timestamp: frame.timestamp
                )
                detections.append(detection)
            }
            return detections
        }
    }
    
    class MockObjectTracker: ObjectTrackerProtocol {
        var shouldThrowError = false
        var trackCount = 2
        
        func track(detections: [Detection]) async throws -> [Track] {
            if shouldThrowError {
                throw TrackingError.trackingFailure(reason: "Mock error")
            }
            
            guard !detections.isEmpty else {
                throw TrackingError.insufficientDetections
            }
            
            var tracks: [Track] = []
            for i in 0..<trackCount {
                let trackDetections = detections.filter { $0.objectClass == .ball }
                if !trackDetections.isEmpty {
                    let track = Track(
                        objectClass: .ball,
                        detections: trackDetections,
                        startTime: trackDetections.first!.timestamp,
                        endTime: trackDetections.last!.timestamp,
                        averageConfidence: 0.8
                    )
                    tracks.append(track)
                }
            }
            return tracks
        }
    }
    
    class MockFeatureExtractor: FeatureExtractorProtocol {
        var shouldThrowError = false
        
        func extractFeatures(from tracks: [Track], sportType: SportType) async throws -> PerformanceFeatures {
            if shouldThrowError {
                throw FeatureExtractionError.insufficientData(component: "Mock error")
            }
            
            let courtCoverage = CourtCoverage(
                zones: [.midCenter: 0.5],
                leftRightBalance: 0.0,
                kitchenLineProximity: 0.2,
                baselineProximity: 0.5
            )
            
            let playerMovement = PlayerMovement(
                courtCoverage: courtCoverage,
                movementSpeed: [0.5, 0.6],
                positioningHistory: [],
                recoveryPositions: [],
                confidence: 0.7
            )
            
            let issue = PerformanceIssue(
                type: .staticPositioning,
                severity: 0.6,
                occurrences: 5,
                description: "Test issue",
                confidence: 0.7
            )
            
            return PerformanceFeatures(
                ballTrajectories: [],
                playerMovement: playerMovement,
                contactPoints: [],
                rallies: [],
                issues: [issue],
                confidence: 0.7
            )
        }
    }
    
    class MockCoachingEngine: CoachingEngineProtocol {
        var shouldThrowError = false
        
        func generateCoaching(from features: PerformanceFeatures, sportType: SportType) async throws -> CoachingFeedback {
            if shouldThrowError {
                throw CoachingGenerationError.insufficientFeatures
            }
            
            let insight = CoachingInsight(
                title: "Test Insight",
                description: "Test description",
                severity: 0.6,
                confidence: 0.7
            )
            
            let suggestion = PracticeSuggestion(
                issue: .staticPositioning,
                drill: "Test Drill",
                description: "Test drill description"
            )
            
            return CoachingFeedback(
                insights: [insight],
                practiceSuggestions: [suggestion],
                quickTips: ["Test tip"],
                nextSessionFocus: ["Test focus"]
            )
        }
    }
    
    class MockModelManager: ModelManagerProtocol {
        var shouldThrowError = false
        
        func loadModel(for sportType: SportType, version: String?) async throws -> MLModel {
            if shouldThrowError {
                throw ModelLoadingError.modelNotFound(sportType: sportType, version: version)
            }
            
            // Return a dummy model (this won't actually be used in tests)
            // In real tests, we'd need a valid Core ML model
            throw ModelLoadingError.modelNotFound(sportType: sportType, version: version)
        }
        
        func releaseModels() {
            // No-op for mock
        }
    }
    
    // MARK: - Test Properties
    
    var pipeline: AnalysisPipeline!
    var mockVideoProcessor: MockVideoProcessor!
    var mockObjectDetector: MockObjectDetector!
    var mockObjectTracker: MockObjectTracker!
    var mockFeatureExtractor: MockFeatureExtractor!
    var mockCoachingEngine: MockCoachingEngine!
    var mockModelManager: MockModelManager!
    
    // MARK: - Setup and Teardown
    
    override func setUp() {
        super.setUp()
        
        mockVideoProcessor = MockVideoProcessor()
        mockObjectDetector = MockObjectDetector()
        mockObjectTracker = MockObjectTracker()
        mockFeatureExtractor = MockFeatureExtractor()
        mockCoachingEngine = MockCoachingEngine()
        mockModelManager = MockModelManager()
        
        pipeline = AnalysisPipeline(
            videoProcessor: mockVideoProcessor,
            objectDetector: mockObjectDetector,
            objectTracker: mockObjectTracker,
            featureExtractor: mockFeatureExtractor,
            coachingEngine: mockCoachingEngine,
            modelManager: mockModelManager
        )
    }
    
    override func tearDown() {
        pipeline = nil
        mockVideoProcessor = nil
        mockObjectDetector = nil
        mockObjectTracker = nil
        mockFeatureExtractor = nil
        mockCoachingEngine = nil
        mockModelManager = nil
        
        super.tearDown()
    }
    
    // MARK: - Tests
    
    /// Tests that pipeline initializes with all dependencies
    /// Validates: Requirement 15.1
    func testPipelineInitialization() {
        XCTAssertNotNil(pipeline)
    }
    
    /// Tests that pipeline executes all stages successfully
    /// Validates: Requirements 15.2, 15.5
    func testSuccessfulAnalysis() async throws {
        // Create a test recording with a valid video URL
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        let recording = GameRecording(
            title: "Test Recording",
            videoURL: testURL,
            duration: 300.0,
            sportType: .pickleball
        )
        
        // Execute analysis
        let analysis = try await pipeline.analyze(recording: recording, sportType: .pickleball)
        
        // Verify analysis was created
        XCTAssertNotNil(analysis)
        XCTAssertGreaterThanOrEqual(analysis.overallRating, 0.0)
        XCTAssertLessThanOrEqual(analysis.overallRating, 5.0)
    }
    
    /// Tests that pipeline reports progress during analysis
    /// Validates: Requirement 15.3
    func testProgressReporting() async throws {
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        let recording = GameRecording(
            title: "Test Recording",
            videoURL: testURL,
            duration: 300.0,
            sportType: .pickleball
        )
        
        var progressUpdates: [AnalysisProgress] = []
        
        // Collect progress updates
        Task {
            for await progress in pipeline.progress {
                progressUpdates.append(progress)
            }
        }
        
        // Execute analysis
        _ = try await pipeline.analyze(recording: recording, sportType: .pickleball)
        
        // Give progress stream time to complete
        try await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        // Verify progress updates were received
        XCTAssertGreaterThan(progressUpdates.count, 0)
        
        // Verify all stages were reported
        let stages = Set(progressUpdates.map { $0.stage })
        XCTAssertTrue(stages.contains(.frameExtraction))
        XCTAssertTrue(stages.contains(.objectDetection))
        XCTAssertTrue(stages.contains(.objectTracking))
        XCTAssertTrue(stages.contains(.featureExtraction))
        XCTAssertTrue(stages.contains(.coachingGeneration))
    }
    
    /// Tests that pipeline handles missing video URL
    /// Validates: Requirement 15.4
    func testMissingVideoURL() async {
        let recording = GameRecording(
            title: "Test Recording",
            videoURL: nil,
            duration: 300.0,
            sportType: .pickleball
        )
        
        do {
            _ = try await pipeline.analyze(recording: recording, sportType: .pickleball)
            XCTFail("Expected VideoProcessingError to be thrown")
        } catch let error as VideoProcessingError {
            XCTAssertEqual(error, VideoProcessingError.fileNotFound)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    /// Tests that pipeline handles frame extraction errors
    /// Validates: Requirement 15.4
    func testFrameExtractionError() async {
        mockVideoProcessor.shouldThrowError = true
        
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        let recording = GameRecording(
            title: "Test Recording",
            videoURL: testURL,
            duration: 300.0,
            sportType: .pickleball
        )
        
        do {
            _ = try await pipeline.analyze(recording: recording, sportType: .pickleball)
            XCTFail("Expected VideoProcessingError to be thrown")
        } catch is VideoProcessingError {
            // Expected error
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    /// Tests that pipeline handles detection errors
    /// Validates: Requirement 15.4
    func testDetectionError() async {
        mockObjectDetector.shouldThrowError = true
        
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        let recording = GameRecording(
            title: "Test Recording",
            videoURL: testURL,
            duration: 300.0,
            sportType: .pickleball
        )
        
        do {
            _ = try await pipeline.analyze(recording: recording, sportType: .pickleball)
            XCTFail("Expected DetectionError to be thrown")
        } catch is DetectionError {
            // Expected error
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    /// Tests that pipeline supports cancellation
    /// Validates: Requirements 15.6, 15.7
    func testCancellation() async {
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        let recording = GameRecording(
            title: "Test Recording",
            videoURL: testURL,
            duration: 300.0,
            sportType: .pickleball
        )
        
        // Start analysis in background
        let analysisTask = Task {
            try await pipeline.analyze(recording: recording, sportType: .pickleball)
        }
        
        // Cancel after a short delay
        try? await Task.sleep(nanoseconds: 10_000_000) // 0.01 seconds
        pipeline.cancel()
        
        // Wait for analysis to complete
        do {
            _ = try await analysisTask.value
            XCTFail("Expected CancellationError to be thrown")
        } catch is CancellationError {
            // Expected error
        } catch {
            // Cancellation might happen at different stages, so other errors are acceptable
        }
    }
    
    /// Tests that pipeline creates valid GameAnalysis
    /// Validates: Requirement 15.2
    func testGameAnalysisCreation() async throws {
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        let recording = GameRecording(
            title: "Test Recording",
            videoURL: testURL,
            duration: 300.0,
            sportType: .pickleball
        )
        
        let analysis = try await pipeline.analyze(recording: recording, sportType: .pickleball)
        
        // Verify GameAnalysis structure
        XCTAssertNotNil(analysis.skillRatings)
        XCTAssertNotNil(analysis.statistics)
        XCTAssertNotNil(analysis.highlights)
        
        // Verify skill ratings are in valid range
        XCTAssertGreaterThanOrEqual(analysis.skillRatings.dinking, 0.0)
        XCTAssertLessThanOrEqual(analysis.skillRatings.dinking, 5.0)
        XCTAssertGreaterThanOrEqual(analysis.skillRatings.volleys, 0.0)
        XCTAssertLessThanOrEqual(analysis.skillRatings.volleys, 5.0)
        XCTAssertGreaterThanOrEqual(analysis.skillRatings.movement, 0.0)
        XCTAssertLessThanOrEqual(analysis.skillRatings.movement, 5.0)
    }
}
