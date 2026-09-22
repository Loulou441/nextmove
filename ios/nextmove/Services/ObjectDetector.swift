//
//  ObjectDetector.swift
//  nextmove
//
//  Object detection service using Vision framework and Core ML models
//  Validates: Requirements 2.1-2.10, 14.1-14.5
//

import Foundation
import CoreML
import Vision
import CoreGraphics
import AVFoundation
import os.log

/// Identifies objects in video frames using Core ML models via Vision framework
/// Validates: Requirements 2.1-2.10, 14.1-14.5
final class ObjectDetector: ObjectDetectorProtocol {
    
    // MARK: - Properties
    
    /// Model manager for loading Core ML models
    private let modelManager: ModelManagerProtocol
    
    /// Confidence threshold for filtering detections (default 0.3)
    private let confidenceThreshold: Float
    
    /// Logger for debugging and observability
    private let logger = Logger(subsystem: "com.nextmove.cvml", category: "ObjectDetector")
    
    /// Cache of Vision requests by sport type
    private var requestCache: [SportType: VNCoreMLRequest] = [:]
    
    /// Lock for thread-safe cache access
    private let cacheLock = NSLock()
    
    // MARK: - Initialization
    
    /// Initializes the object detector with a model manager
    /// - Parameters:
    ///   - modelManager: Model manager for loading Core ML models
    ///   - confidenceThreshold: Minimum confidence threshold for detections (default 0.3)
    init(modelManager: ModelManagerProtocol, confidenceThreshold: Float = 0.3) {
        self.modelManager = modelManager
        self.confidenceThreshold = confidenceThreshold
    }
    
    // MARK: - ObjectDetectorProtocol Implementation
    
    /// Detects objects in a single video frame
    /// Validates: Requirements 2.1-2.10, 14.1, 14.3, 14.4
    /// - Parameters:
    ///   - frame: The video frame to analyze
    ///   - sportType: Sport type for loading appropriate detection model
    /// - Returns: Array of detections with bounding boxes and confidence scores
    /// - Throws: ModelLoadingError, DetectionError
    func detect(in frame: VideoFrame, sportType: SportType) async throws -> [Detection] {
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Get or create Vision request for this sport type
        let request = try await getOrCreateRequest(for: sportType)
        
        // Create image request handler
        let handler = VNImageRequestHandler(cgImage: frame.image, options: [:])
        
        // Perform detection
        do {
            try handler.perform([request])
        } catch {
            logger.error("Vision request failed: \(error.localizedDescription)")
            throw DetectionError.inferenceFailure(reason: error.localizedDescription)
        }
        
        // Parse results
        guard let results = request.results as? [VNRecognizedObjectObservation] else {
            logger.warning("No detection results for frame \(frame.frameNumber)")
            return []
        }
        
        // Convert Vision results to Detection objects
        let detections = results.compactMap { observation in
            convertToDetection(
                observation: observation,
                frameNumber: frame.frameNumber,
                timestamp: frame.timestamp
            )
        }
        
        // Filter by confidence threshold
        let filteredDetections = detections.filter { $0.confidence >= confidenceThreshold }
        
        // Sort by confidence (highest first)
        let sortedDetections = filteredDetections.sorted { $0.confidence > $1.confidence }
        
        let elapsedTime = CFAbsoluteTimeGetCurrent() - startTime
        logger.debug("Detected \(sortedDetections.count) objects in frame \(frame.frameNumber) (\(String(format: "%.3f", elapsedTime))s)")
        
        // Validate performance target (< 200ms)
        if elapsedTime > 0.2 {
            logger.warning("Detection exceeded 200ms target: \(String(format: "%.3f", elapsedTime))s")
        }
        
        return sortedDetections
    }
    
    // MARK: - Private Methods
    
    /// Gets or creates a Vision Core ML request for the specified sport type
    /// Validates: Requirements 14.1, 13.1, 13.7
    private func getOrCreateRequest(for sportType: SportType) async throws -> VNCoreMLRequest {
        // Check cache first
        cacheLock.lock()
        if let cachedRequest = requestCache[sportType] {
            cacheLock.unlock()
            return cachedRequest
        }
        cacheLock.unlock()
        
        // Load model from model manager
        let model = try await modelManager.loadModel(for: sportType, version: nil)
        
        // Create Vision Core ML model
        guard let visionModel = try? VNCoreMLModel(for: model) else {
            logger.error("Failed to create Vision model for \(sportType.rawValue)")
            throw DetectionError.inferenceFailure(reason: "Failed to create Vision model")
        }
        
        // Create Vision Core ML request
        let request = VNCoreMLRequest(model: visionModel) { [weak self] request, error in
            if let error = error {
                self?.logger.error("Vision request error: \(error.localizedDescription)")
            }
        }
        
        // Configure request
        request.imageCropAndScaleOption = .scaleFill
        
        // Cache the request
        cacheLock.lock()
        requestCache[sportType] = request
        cacheLock.unlock()
        
        logger.info("Created Vision request for \(sportType.rawValue)")
        
        return request
    }
    
    /// Converts a Vision observation to a Detection object
    /// Validates: Requirements 2.1-2.7, 14.3
    private func convertToDetection(
        observation: VNRecognizedObjectObservation,
        frameNumber: Int,
        timestamp: CMTime
    ) -> Detection? {
        // Get the top label (highest confidence class)
        guard let topLabel = observation.labels.first else {
            logger.warning("Observation has no labels")
            return nil
        }
        
        // Parse object class from label
        guard let objectClass = parseObjectClass(from: topLabel.identifier) else {
            logger.warning("Unknown object class: \(topLabel.identifier)")
            return nil
        }
        
        // Get bounding box (Vision uses normalized coordinates 0-1, origin at bottom-left)
        let visionBoundingBox = observation.boundingBox
        
        // Convert Vision coordinates (bottom-left origin) to standard coordinates (top-left origin)
        // Vision: (0,0) is bottom-left, (1,1) is top-right
        // Standard: (0,0) is top-left, (1,1) is bottom-right
        let normalizedBoundingBox = CGRect(
            x: visionBoundingBox.minX,
            y: 1.0 - visionBoundingBox.maxY, // Flip Y coordinate
            width: visionBoundingBox.width,
            height: visionBoundingBox.height
        )
        
        // Get confidence score
        let confidence = topLabel.confidence
        
        // Create Detection object
        return Detection(
            id: UUID(),
            objectClass: objectClass,
            boundingBox: normalizedBoundingBox,
            confidence: confidence,
            frameNumber: frameNumber,
            timestamp: timestamp
        )
    }
    
    /// Parses an ObjectClass from a label identifier string
    /// Validates: Requirements 2.1-2.6
    private func parseObjectClass(from identifier: String) -> ObjectClass? {
        // Normalize identifier (lowercase, remove spaces/underscores)
        let normalized = identifier.lowercased()
            .replacingOccurrences(of: "_", with: "")
            .replacingOccurrences(of: " ", with: "")
        
        // Map to ObjectClass. Handles naming variants across datasets, e.g.
        // "tennis ball" -> "tennisball", "Player" -> "player".
        switch normalized {
        case "ball", "tennisball", "sportsball":
            return .ball
        case "player", "person", "player1", "player2":
            // Some datasets label players individually (player1/player2);
            // the app treats all of them as the generic player class.
            return .player
        case "paddle", "racket", "tennisracket":
            return .paddle
        case "courtline", "court":
            return .courtLine
        case "net":
            return .net
        case "netpost", "post":
            return .netPost
        default:
            return nil
        }
    }
    
    /// Releases cached Vision requests to free memory
    func releaseCache() {
        cacheLock.lock()
        requestCache.removeAll()
        cacheLock.unlock()
        
        logger.info("Released Vision request cache")
    }
}

// MARK: - Performance Monitoring

extension ObjectDetector {
    
    /// Validates that detection performance meets the < 200ms target
    /// Validates: Requirements 2.8
    func validatePerformance(detectionTime: TimeInterval) -> Bool {
        return detectionTime < 0.2
    }
}
