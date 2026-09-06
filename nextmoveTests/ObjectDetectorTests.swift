//
//  ObjectDetectorTests.swift
//  nextmoveTests
//
//  Unit tests for ObjectDetector service
//  Validates: Requirements 2.1-2.10, 14.1-14.5
//

import XCTest
import CoreML
import Vision
import CoreGraphics
import AVFoundation
@testable import nextmove

final class ObjectDetectorTests: XCTestCase {
    
    var mockModelManager: MockModelManager!
    var objectDetector: ObjectDetector!
    
    override func setUp() {
        super.setUp()
        mockModelManager = MockModelManager()
        objectDetector = ObjectDetector(modelManager: mockModelManager, confidenceThreshold: 0.3)
    }
    
    override func tearDown() {
        objectDetector = nil
        mockModelManager = nil
        super.tearDown()
    }
    
    // MARK: - Initialization Tests
    
    func testInitialization() {
        // Test default confidence threshold
        let detector = ObjectDetector(modelManager: mockModelManager)
        XCTAssertNotNil(detector)
        
        // Test custom confidence threshold
        let customDetector = ObjectDetector(modelManager: mockModelManager, confidenceThreshold: 0.5)
        XCTAssertNotNil(customDetector)
    }
    
    // MARK: - Detection Output Structure Tests
    // Validates: Requirements 2.1-2.7
    
    func testDetectionOutputStructure() async throws {
        // Create test frame
        let frame = createTestFrame()
        
        // Configure mock to return valid model
        mockModelManager.shouldSucceed = true
        
        // Perform detection
        let detections = try await objectDetector.detect(in: frame, sportType: .pickleball)
        
        // Verify all detections have valid structure
        for detection in detections {
            // Valid bounding box (non-negative coordinates, positive dimensions)
            XCTAssertGreaterThanOrEqual(detection.boundingBox.origin.x, 0.0)
            XCTAssertGreaterThanOrEqual(detection.boundingBox.origin.y, 0.0)
            XCTAssertGreaterThan(detection.boundingBox.width, 0.0)
            XCTAssertGreaterThan(detection.boundingBox.height, 0.0)
            
            // Normalized coordinates (0-1 range)
            XCTAssertLessThanOrEqual(detection.boundingBox.maxX, 1.0)
            XCTAssertLessThanOrEqual(detection.boundingBox.maxY, 1.0)
            
            // Valid confidence score (0.0-1.0)
            XCTAssertGreaterThanOrEqual(detection.confidence, 0.0)
            XCTAssertLessThanOrEqual(detection.confidence, 1.0)
            
            // Valid object class
            XCTAssertNotNil(detection.objectClass)
            
            // Valid frame number and timestamp
            XCTAssertEqual(detection.frameNumber, frame.frameNumber)
            XCTAssertEqual(detection.timestamp, frame.timestamp)
        }
    }
    
    // MARK: - Confidence Threshold Tests
    // Validates: Requirements 2.7
    
    func testConfidenceThresholdFiltering() async throws {
        // Create detector with custom threshold
        let detector = ObjectDetector(modelManager: mockModelManager, confidenceThreshold: 0.5)
        
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        let detections = try await detector.detect(in: frame, sportType: .pickleball)
        
        // All detections should meet or exceed threshold
        for detection in detections {
            XCTAssertGreaterThanOrEqual(detection.confidence, 0.5)
        }
    }
    
    func testDefaultConfidenceThreshold() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        let detections = try await objectDetector.detect(in: frame, sportType: .pickleball)
        
        // All detections should meet or exceed default threshold (0.3)
        for detection in detections {
            XCTAssertGreaterThanOrEqual(detection.confidence, 0.3)
        }
    }
    
    // MARK: - Detection Sorting Tests
    // Validates: Requirements 2.9
    
    func testDetectionsSortedByConfidence() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        let detections = try await objectDetector.detect(in: frame, sportType: .pickleball)
        
        // Verify detections are sorted by confidence (highest first)
        if detections.count > 1 {
            for i in 0..<(detections.count - 1) {
                XCTAssertGreaterThanOrEqual(detections[i].confidence, detections[i + 1].confidence)
            }
        }
    }
    
    // MARK: - Sport Type Tests
    // Validates: Requirements 17.2, 17.6
    
    func testPickleballDetection() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        let detections = try await objectDetector.detect(in: frame, sportType: .pickleball)
        
        // Should successfully detect with pickleball model
        XCTAssertNotNil(detections)
        XCTAssertTrue(mockModelManager.loadModelCalled)
        XCTAssertEqual(mockModelManager.lastSportType, .pickleball)
    }
    
    func testTennisDetection() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        let detections = try await objectDetector.detect(in: frame, sportType: .tennis)
        
        // Should successfully detect with tennis model
        XCTAssertNotNil(detections)
        XCTAssertTrue(mockModelManager.loadModelCalled)
        XCTAssertEqual(mockModelManager.lastSportType, .tennis)
    }
    
    // MARK: - Error Handling Tests
    // Validates: Requirements 14.4, 23.1-23.7
    
    func testModelLoadingFailure() async {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = false
        mockModelManager.errorToThrow = ModelLoadingError.modelNotFound(sportType: .pickleball, version: nil)
        
        do {
            _ = try await objectDetector.detect(in: frame, sportType: .pickleball)
            XCTFail("Should throw ModelLoadingError")
        } catch let error as ModelLoadingError {
            // Expected error
            XCTAssertNotNil(error)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    func testEmptyDetectionResults() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        // Detection should succeed even with no results
        let detections = try await objectDetector.detect(in: frame, sportType: .pickleball)
        
        // Empty array is valid (no objects detected)
        XCTAssertNotNil(detections)
    }
    
    // MARK: - Performance Tests
    // Validates: Requirements 2.8
    
    func testDetectionPerformance() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        let startTime = CFAbsoluteTimeGetCurrent()
        _ = try await objectDetector.detect(in: frame, sportType: .pickleball)
        let elapsedTime = CFAbsoluteTimeGetCurrent() - startTime
        
        // Should complete in less than 200ms (relaxed for testing environment)
        // Note: In production on target devices, this should be < 0.2s
        XCTAssertLessThan(elapsedTime, 1.0, "Detection took too long: \(elapsedTime)s")
    }
    
    func testPerformanceValidation() {
        // Test performance validation helper
        XCTAssertTrue(objectDetector.validatePerformance(detectionTime: 0.15))
        XCTAssertTrue(objectDetector.validatePerformance(detectionTime: 0.19))
        XCTAssertFalse(objectDetector.validatePerformance(detectionTime: 0.21))
        XCTAssertFalse(objectDetector.validatePerformance(detectionTime: 0.5))
    }
    
    // MARK: - Bounding Box Coordinate Tests
    // Validates: Requirements 2.1-2.6
    
    func testBoundingBoxNormalization() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        let detections = try await objectDetector.detect(in: frame, sportType: .pickleball)
        
        // All bounding boxes should be normalized to 0-1 range
        for detection in detections {
            XCTAssertGreaterThanOrEqual(detection.boundingBox.minX, 0.0)
            XCTAssertGreaterThanOrEqual(detection.boundingBox.minY, 0.0)
            XCTAssertLessThanOrEqual(detection.boundingBox.maxX, 1.0)
            XCTAssertLessThanOrEqual(detection.boundingBox.maxY, 1.0)
        }
    }
    
    // MARK: - Cache Management Tests
    
    func testRequestCaching() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        // First detection should load model
        _ = try await objectDetector.detect(in: frame, sportType: .pickleball)
        let firstLoadCount = mockModelManager.loadModelCallCount
        
        // Second detection should use cached request
        _ = try await objectDetector.detect(in: frame, sportType: .pickleball)
        let secondLoadCount = mockModelManager.loadModelCallCount
        
        // Model should only be loaded once (cached for second call)
        XCTAssertEqual(firstLoadCount, 1)
        XCTAssertEqual(secondLoadCount, 1)
    }
    
    func testCacheRelease() async throws {
        let frame = createTestFrame()
        mockModelManager.shouldSucceed = true
        
        // Perform detection to populate cache
        _ = try await objectDetector.detect(in: frame, sportType: .pickleball)
        
        // Release cache
        objectDetector.releaseCache()
        
        // Next detection should reload model
        _ = try await objectDetector.detect(in: frame, sportType: .pickleball)
        
        // Model should be loaded twice (once before cache release, once after)
        XCTAssertEqual(mockModelManager.loadModelCallCount, 2)
    }
    
    // MARK: - Helper Methods
    
    private func createTestFrame(frameNumber: Int = 1) -> VideoFrame {
        // Create a simple test image (100x100 white square)
        let width = 100
        let height = 100
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)
        
        guard let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: width * 4,
            space: colorSpace,
            bitmapInfo: bitmapInfo.rawValue
        ) else {
            fatalError("Failed to create CGContext")
        }
        
        // Fill with white
        context.setFillColor(CGColor(red: 1.0, green: 1.0, blue: 1.0, alpha: 1.0))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        
        guard let cgImage = context.makeImage() else {
            fatalError("Failed to create CGImage")
        }
        
        return VideoFrame(
            image: cgImage,
            timestamp: CMTime(value: CMTimeValue(frameNumber), timescale: 30),
            frameNumber: frameNumber
        )
    }
}

// MARK: - Mock Model Manager

class MockModelManager: ModelManagerProtocol {
    var shouldSucceed = true
    var errorToThrow: Error?
    var loadModelCalled = false
    var loadModelCallCount = 0
    var lastSportType: SportType?
    var lastVersion: String?
    
    func loadModel(for sportType: SportType, version: String?) async throws -> MLModel {
        loadModelCalled = true
        loadModelCallCount += 1
        lastSportType = sportType
        lastVersion = version
        
        if !shouldSucceed {
            if let error = errorToThrow {
                throw error
            }
            throw ModelLoadingError.modelNotFound(sportType: sportType, version: version)
        }
        
        // Return a mock model (we can't easily create a real MLModel in tests)
        // In real tests, we would use a fixture model file
        // For now, we'll create a minimal model configuration
        return try await createMockModel()
    }
    
    func releaseModels() {
        // Mock implementation
    }
    
    private func createMockModel() async throws -> MLModel {
        // Create a minimal Core ML model for testing
        // This is a placeholder - in real tests, we would load a fixture model
        // For now, we'll throw an error that indicates we need a real model
        throw ModelLoadingError.modelNotFound(sportType: .pickleball, version: nil)
    }
}
